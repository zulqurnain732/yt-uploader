import os
import sys
import json
import random
import subprocess
import time
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# YouTube OAuth Setup
token_info = json.loads(os.environ["YT_TOKEN_JSON"])
creds = Credentials(
    token=None,
    refresh_token=token_info["refresh_token"],
    token_uri=token_info["token_uri"],
    client_id=token_info["client_id"],
    client_secret=token_info["client_secret"]
)
youtube = build("youtube", "v3", credentials=creds)

def download_drive_video(file_id, output_path):
    print("Downloading video from Google Drive...")
    session = requests.Session()
    url = "https://drive.usercontent.google.com/download"
    params = {'id': file_id, 'export': 'download', 'confirm': 't'}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    response = session.get(url, params=params, headers=headers, stream=True)
    
    # Fallback to standard url if needed
    if response.status_code != 200:
        url_alt = "https://docs.google.com/uc?export=download"
        response = session.get(url_alt, params={'id': file_id, 'confirm': 'yes'}, headers=headers, stream=True)
    
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
                
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Downloaded successfully! File size: {file_size_mb:.2f} MB")
    
    if file_size_mb < 1.0:
        raise Exception("Download failed: File size too small (Google Drive virus scan warning block).")

def upload_to_youtube(file_path, title, description, tags, thumbnail_path=None):
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "public"
        }
    }
    
    media = MediaFileUpload(file_path, mimetype="video/mp4", chunksize=1024*1024*5, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploading: {int(status.progress() * 100)}%")
            
    video_id = response.get("id")
    print(f"Uploaded Successfully! Video ID: {video_id}")
    
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
            ).execute()
            print("Thumbnail attached successfully!")
        except Exception as e:
            print(f"Thumbnail notice: {e}")

def run():
    mode = sys.argv[1] if len(sys.argv) > 1 else "video"
    file_id = "1_Xdyd1EQqfmiU-rHj9zQkE6ezZc6Y4Zr"
    raw_video = "source_video.mp4"
    
    if not os.path.exists(raw_video) or os.path.getsize(raw_video) < 1024 * 1024:
        download_drive_video(file_id, raw_video)
        
    part_num = int(time.time()) % 10000
    
    if mode == "video":
        thumb_img = "thumbnail.jpg"
        # Video ke pehle achhe frame se HD thumbnail create karna
        subprocess.run(["ffmpeg", "-y", "-ss", "00:00:03", "-i", raw_video, "-vframes", "1", thumb_img], check=True)
        
        title = f"Surah Ar-Rahman Full Recitation | Beautiful Heart Touching Voice #{part_num}"
        description = (
            "Surah Ar-Rahman (سورة الرحمن) with beautiful heart touching Quran recitation.\n\n"
            "The recitation of Surah Rehman brings tranquility and peace to the soul.\n\n"
            "#SurahRahman #Quran #SurahArRahman #Islamic #QuranRecitation"
        )
        tags = [
            "Surah Rahman", "Surah Ar-Rahman", "Quran Recitation", 
            "Surah Rehman Full", "Beautiful Recitation", "Quran", 
            "Peaceful Quran", "Surah Rahman Recitation", "Islamic"
        ]
        upload_to_youtube
