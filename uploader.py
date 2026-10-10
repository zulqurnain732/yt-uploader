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

def download_drive_file(file_id, output_path):
    print(f"Downloading from Google Drive to {output_path}...")
    session = requests.Session()
    
    # Direct Google Drive streaming URL
    url = "https://drive.usercontent.google.com/download"
    params = {'id': file_id, 'export': 'download', 'confirm': 't'}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    
    response = session.get(url, params=params, headers=headers, stream=True)
    
    # Fallback endpoint agar Google direct block kare
    if response.status_code != 200:
        url_alt = "https://docs.google.com/uc?export=download"
        response = session.get(url_alt, params={'id': file_id, 'confirm': 'yes'}, headers=headers, stream=True)
        
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
                
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Download complete: {output_path} ({file_size_mb:.2f} MB)")
    if file_size_mb < 0.05:
        raise Exception(f"File too small ({file_size_mb:.2f} MB), check Google Drive link sharing permissions.")

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
    
    media = MediaFileUpload(file_path, mimetype="video/mp4", chunksize=1024 * 1024 * 5, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")
            
    video_id = response.get("id")
    print(f"Video uploaded successfully! Video ID: {video_id}")
    
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
            ).execute()
            print("Thumbnail applied successfully!")
        except Exception as e:
            print(f"Thumbnail notice: {e}")

def run():
    mode = sys.argv[1] if len(sys.argv) > 1 else "video"
    
    video_drive_id = "13STb9Kb_PldhzCoxpy9iebpGKsaTkPvs"
    thumb_drive_id = "1_Xdyd1EQqfmiU-rHj9zQkE6ezZc6Y4Zr"
    
    raw_video = "source_video.mp4"
    if not os.path.exists(raw_video) or os.path.getsize(raw_video) < 1024 * 1024:
        download_drive_file(video_drive_id, raw_video)
        
    part_id = int(time.time()) % 10000
    
    if mode == "video":
        thumb_img = "custom_thumbnail.jpg"
        if not os.path.exists(thumb_img):
            download_drive_file(thumb_drive_id, thumb_img)
            
        title = f"Surah Ar-Rahman Full Recitation | Beautiful Heart Touching Voice #{part_id}"
        description = (
            "Surah Ar-Rahman (سورة الرحمن) recitation.\n"
            "Listen to the peaceful and beautiful Quran recitation.\n\n"
            "#SurahRahman #Quran #SurahArRahman #QuranRecitation #Islamic"
        )
        tags = [
            "Surah Rahman", "Surah Ar-Rahman", "Quran Recitation",
            "Surah Rehman Full", "Beautiful Quran Recitation", "Quran Tilawat",
            "Peaceful Recitation", "Islamic"
        ]
        upload_to_youtube(raw_video, title, description, tags, thumbnail_path=thumb_img)
        
    elif mode == "short":
        short_video = "short_clip.mp4"
        start_time = random.randint(15, 60)
        
        # 9:16 Portrait crop for YouTube Shorts
        cmd = [
            "ffmpeg", "-y", "-ss", str(start_time), "-t", "45",
            "-i", raw_video,
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            "-c:a", "aac", "-b:a", "128k",
            short_video
        ]
        subprocess.run(cmd, check=True)
        
        title = f"Surah Ar-Rahman Recitation ❤️ #Shorts #{part_id}"
        description = (
            "Beautiful Quran recitation of Surah Ar-Rahman.\n\n"
            "#Shorts #SurahRahman #Quran #IslamicShorts #QuranRecitation"
        )
        tags = ["Shorts", "Surah Rahman", "Quran", "IslamicShorts", "ViralShorts"]
        upload_to_youtube(short_video, title, description, tags)

if __name__ == "__main__":
    run()
