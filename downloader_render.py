import yt_dlp
import os
import subprocess
from pytubefix import YouTube
import zipfile
import json
import io
import requests

TEMP_DIR="/tmp" #umjesto output_patha na Renderu

def youtube_to_m4a_ffmpeg(url, output_path='.'):
    try:
        print(f"\n📁 Trenutni radni direktorij: {os.getcwd()}")
        yt = YouTube(url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        print(f"🎬 Video: {yt.title}")

        # Preuzmi audio kao .mp4 / .m4a
        downloaded_file = audio_stream.download(output_path=output_path)
        print(f"⬇️  Skinuti fajl: {downloaded_file}")
        print(f"📦 Fajl postoji? {'Da' if os.path.exists(downloaded_file) else 'Ne'}")
        print("✅ Stvoren je konacni m4a file")
        print(os.path.abspath(downloaded_file))
        return os.path.abspath(downloaded_file)

        
    except Exception as e:
        print("❗ Došlo je do greške:", e)


def search_youtube(query, max_results=1): # EXTRACT VIDEO FROM TEXT
    search_query = f"ytsearch{max_results}:{query}"
    
    options = {
        'quiet': True,
        'skip_download': True,
        'extract_flat': True,  # True - brze (bez thumbnaila), False - s thumbnailom
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        results = ydl.extract_info(search_query, download=False)
        videos = results.get('entries', [])
        return videos
    print("drugi dio gotov")

def get_thumbnail_url(youtube_url: str) -> str:
    """
    Vraća URL maxres thumbnaila s YouTube videa.
    Podržava linkove tipa:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - samo VIDEO_ID
    """
    if "youtu.be/" in youtube_url:
        video_id = youtube_url.split("/")[-1]
    elif "watch?v=" in youtube_url:
        video_id = youtube_url.split("watch?v=")[-1].split("&")[0]
    else:
        # Pretpostavlja da je samo ID
        video_id = youtube_url

    #moguca greska
    return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg" 
    #return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    #taj drugi uvijek postoji
def main_function(query,output_path='.'):
    mem = io.BytesIO()
    
    results = search_youtube(query)
    
    print("\nRezultati:")
    for i, video in enumerate(results, start=1):
        title = video.get('title', 'Untitled')
        author = video.get('uploader', 'Unknown')
        url = video.get('url', 'N/A')
        thumbnail=get_thumbnail_url(url)
        print(f"{i}. {title}")
        print(f"   Artist: {author}\n")
        print(f"   URL: {url}\n")
        print(f"   Thumbnail: {get_thumbnail_url(url)}\n")

    resp = requests.get(get_thumbnail_url(url))
    thumbnail_bytes = resp.content
    
    with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Dodaj m4a fajl
        with open(youtube_to_m4a_ffmpeg(url, output_path), "rb") as f:
            data = f.read()
        zf.writestr("song.m4a", data)
        
        # Dodaj thumbnail
        zf.writestr("thumbnail.jpg", thumbnail_bytes)
        
        # Dodaj metapodatke u JSON formatu
        metadata = {
            "title": title,
            "author": author
        }
        zf.writestr("info.json", json.dumps(metadata, ensure_ascii=False))
    
    mem.seek(0)
    print("ended zip")

    zip_path = os.path.abspath(os.path.join(output_path, "output.zip"))
    with open(zip_path, "wb") as f:
        f.write(mem.getbuffer())

    print(zip_path)

    return zip_path   # vraća path do fajla

