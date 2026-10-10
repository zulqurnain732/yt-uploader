import os
import sys
import json
import random
import subprocess
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# YouTube hitelesítés beállítása a Secretből
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
    url = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(url, params={'id': file_id}, stream=True)
    
    token = None
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            token = value
            break
            
    if token:
        params = {'id': file_id, 'confirm': token}
        response = session.get(url, params=params, stream=True)
        
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)
    print(f"Sikeres letöltés: {output_path}")

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
    
    media = MediaFileUpload(file_path, chunksize=1024*1024*5, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Feltöltés állapota: {int(status.progress() * 100)}%")
            
    video_id = response.get("id")
    print(f"Videó sikeresen feltöltve! Videó azonosító: {video_id}")
    
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            print("Indexkép sikeresen beállítva!")
        except Exception as e:
            print(f"Indexkép hiba (kihagyva): {e}")

def run():
    mode = sys.argv[1] if len(sys.argv) > 1 else "video"
    file_id = "1_Xdyd1EQqfmiU-rHj9zQkE6ezZc6Y4Zr"
    
    raw_video = "source_video.mp4"
    if not os.path.exists(raw_video) or os.path.getsize(raw_video) < 1000:
        download_drive_file(file_id, raw_video)
        
    if mode == "video":
        thumb_img = "thumbnail.jpg"
        download_drive_file(file_id, thumb_img)
        
        title = "Viral Must-Watch Video Highlight"
        description = "Enjoy this video. Like and subscribe!\n\n#viral #trending"
        tags = ["viral", "trending", "video"]
        upload_to_youtube(raw_video, title, description, tags, thumbnail_path=thumb_img)
        
    elif mode == "short":
        short_video = "short_clip.mp4"
        start_time = random.randint(0, 20)
        
        # 9:16 arányú kivágás YouTube Shorts formátumhoz
        cmd = [
            "ffmpeg", "-y", "-ss", str(start_time), "-t", "40",
            "-i", raw_video,
            "-vf", "crop=ih*(9/16):ih,scale=1080:1920",
            "-c:a", "copy",
            short_video
        ]
        subprocess.run(cmd, check=True)
        
        title = "Amazing Moment #Shorts"
        description = "Viral clip. #Shorts #viral #trending"
        tags = ["shorts", "viral", "trending"]
        upload_to_youtube(short_video, title, description, tags)

if __name__ == "__main__":
    run()
    
