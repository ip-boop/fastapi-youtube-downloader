import yt_dlp
import os
import subprocess
from pytubefix import YouTube
import zipfile
import json
import io
import requests
import ffmpeg

TEMP_DIR="/tmp" #umjesto output_patha na Renderu


def youtube_to_m4a_yt_dlp(url, output_path=TEMP_DIR):
    output_template = os.path.join(output_path, "%(title)s.%(ext)s")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
            'preferredquality': '192',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        audio_file = ydl.prepare_filename(info)
        # promijeni ekstenziju u m4a ako je ffmpeg postprocesirao
        if not audio_file.endswith(".m4a"):
            audio_file = os.path.splitext(audio_file)[0] + ".m4a"
        return audio_file


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

def main_function(query, output_path=TEMP_DIR):
    mem = io.BytesIO()

    # Pretraži YouTube koristeći yt-dlp
    search_query = f"ytsearch1:{query}"
    ydl_opts = {'quiet': True, 'skip_download': True, 'extract_flat': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        results = ydl.extract_info(search_query, download=False).get('entries', [])

    if not results:
        raise Exception("Nema rezultata za upit!")

    video = results[0]
    title = video.get('title', 'Untitled')
    author = video.get('uploader', 'Unknown')
    url = video.get('url', 'N/A')

    # Preuzmi audio
    audio_file = youtube_to_m4a_yt_dlp(url, output_path)

    # Preuzmi thumbnail
    thumbnail_url = f"https://img.youtube.com/vi/{video['id']}/maxresdefault.jpg"
    resp = requests.get(thumbnail_url)
    thumbnail_bytes = resp.content

    # Kreiraj zip
    with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        with open(audio_file, "rb") as f:
            zf.writestr("song.m4a", f.read())
        zf.writestr("thumbnail.jpg", thumbnail_bytes)
        metadata = {"title": title, "author": author}
        zf.writestr("info.json", json.dumps(metadata, ensure_ascii=False))

    mem.seek(0)
    zip_path = os.path.join(output_path, "output.zip")
    with open(zip_path, "wb") as f:
        f.write(mem.getbuffer())

    # Očisti privremeni audio fajl
    if os.path.exists(audio_file):
        os.remove(audio_file)
    return zip_path

