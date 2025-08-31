import yt_dlp
import os
from pytubefix import YouTube
import zipfile
import json
import io
import requests

TEMP_DIR = "/tmp"  # na Renderu uvijek postoji i resetira se kod redeploya

def youtube_to_m4a_ffmpeg(url, output_path=TEMP_DIR):
    try:
        print(f"\n📁 Trenutni radni direktorij: {os.getcwd()}")
        yt = YouTube(url,use_po_token=True)
        audio_stream = yt.streams.filter(only_audio=True).first()
        print(f"🎬 Video: {yt.title}")

        # Preuzmi audio u /tmp
        downloaded_file = audio_stream.download(output_path=output_path)
        print(f"⬇️ Skinuti fajl: {downloaded_file}")
        return os.path.abspath(downloaded_file)

    except Exception as e:
        print("❗ Došlo je do greške:", e)
        raise


def search_youtube(query, max_results=1):
    search_query = f"ytsearch{max_results}:{query}"
    
    options = {
        'quiet': True,
        'skip_download': True,
        'extract_flat': True,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        results = ydl.extract_info(search_query, download=False)
        return results.get('entries', [])


def get_thumbnail_url(youtube_url: str) -> str:
    if "youtu.be/" in youtube_url:
        video_id = youtube_url.split("/")[-1]
    elif "watch?v=" in youtube_url:
        video_id = youtube_url.split("watch?v=")[-1].split("&")[0]
    else:
        video_id = youtube_url
    return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"


def main_function(query, output_path=TEMP_DIR):
    mem = io.BytesIO()
    
    results = search_youtube(query)
    if not results:
        raise Exception("Nema rezultata za upit!")

    video = results[0]  # uzmi prvi rezultat
    title = video.get('title', 'Untitled')
    author = video.get('uploader', 'Unknown')
    url = video.get('url', 'N/A')

    print(f"Video: {title} | Autor: {author} | URL: {url}")

    resp = requests.get(get_thumbnail_url(url))
    thumbnail_bytes = resp.content
    
    # preuzmi audio u /tmp
    audio_file = youtube_to_m4a_ffmpeg(url, output_path=TEMP_DIR)

    try:
        with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            # Dodaj m4a fajl
            with open(audio_file, "rb") as f:
                zf.writestr("song.m4a", f.read())
            
            # Dodaj thumbnail
            zf.writestr("thumbnail.jpg", thumbnail_bytes)
            
            # Dodaj metapodatke
            metadata = {"title": title, "author": author}
            zf.writestr("info.json", json.dumps(metadata, ensure_ascii=False))
    finally:
        # obriši privremeni audio fajl
        try:
            if os.path.exists(audio_file):
                os.remove(audio_file)
                print(f"🗑️ Obrisan temp fajl: {audio_file}")
        except Exception as e:
            print(f"⚠️ Greška pri brisanju fajla: {e}")

    mem.seek(0)

    # Spremi zip u /tmp (da app_fastapi može streamati s diska)
    zip_path = os.path.abspath(os.path.join(output_path, "output.zip"))
    with open(zip_path, "wb") as f:
        f.write(mem.getbuffer())

    return zip_path
