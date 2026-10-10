import os
import sys
import json
import random
import subprocess
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# YouTube OAuth Auth Setup
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
    # yt-dlp ke zariye direct clean video download taake corrupt HTML file na aaye
    drive_url = f"https://drive.google.com/file/d/{file_id}/view"
    subprocess.run(["yt-dlp", "-o", output_path, drive_url], check=True)
    print(f"Video file downloaded cleanly to {output_path}")

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
    print(f"Video Uploaded Successfully! ID: {video_id}")
    
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
            ).execute()
            print("Thumbnail Attached Successfully!")
        except Exception as e:
            print(f"Thumbnail note: {e}")

def run():
    mode = sys.argv[1] if len(sys.argv) > 1 else "video"
    file_id = "1_Xdyd1EQqfmiU-rHj9zQkE6ezZc6Y4Zr"
    raw_video = "source_video.mp4"
    
    if not os.path.exists(raw_video) or os.path.getsize(raw_video) < 50000:
        download_drive_video(file_id, raw_video)
        
    part_num = int(time.time()) % 10000
    
    if mode == "video":
        thumb_img = "thumbnail.jpg"
        # First frame ko high quality thumbnail k tor par extract karein
        subprocess.run(["ffmpeg", "-y", "-ss", "00:00:05", "-i", raw_video, "-vframes", "1", thumb_img], check=True)
        
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
        upload_to_youtube(raw_video, title, description, tags, thumbnail_path=thumb_img)
        
    elif mode == "short":
        short_video = "short_clip.mp4"
        start_time = random.randint(10, 45)
        
        # 9:16 vertical crop with standard h264/aac encoding for YouTube Shorts
        cmd = [
            "ffmpeg", "-y", "-ss", str(start_time), "-t", "45",
            "-i", raw_video,
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "aac", "-b:a", "128k",
            short_video
        ]
        subprocess.run(cmd, check=True)
        
        title = f"Surah Ar-Rahman Recitation ❤️ #Shorts #{part_num}"
        description = (
            "Most beautiful Quran recitation - Surah Ar-Rahman.\n\n"
            "#Shorts #SurahRahman #Quran #IslamicShorts #QuranRecitation"
        )
        tags = ["Shorts", "Surah Rahman", "Quran", "IslamicShorts", "ViralShorts"]
        upload_to_youtube(short_video, title, description, tags)

if __name__ == "__main__":
    run()
