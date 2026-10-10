import os
import sys
import json
import random
import subprocess
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

token_info = json.loads(os.environ["YT_TOKEN_JSON"])
creds = Credentials(
    token=None,
    refresh_token=token_info["refresh_token"],
    token_uri=token_info["token_uri"],
    client_id=token_info["client_id"],
    client_secret=token_info["client_secret"]
)
youtube = build("youtube", "v3", credentials=creds)

def download_file(file_id, output_path):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    subprocess.run(["gdown", "--fuzzy", url, "-O", output_path], check=True)

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
    
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    video_id = response.get("id")
    print(f"Uploaded successfully! ID: {video_id}")
    
    if thumbnail_path and os.path.exists(thumbnail_path):
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path)
        ).execute()
        print("Thumbnail attached successfully!")

def run():
    mode = sys.argv[1] if len(sys.argv) > 1 else "video"
    file_id = "1_Xdyd1EQqfmiU-rHj9zQkE6ezZc6Y4Zr"
    
    raw_video = "source_video.mp4"
    if not os.path.exists(raw_video):
        download_file(file_id, raw_video)
        
    if mode == "video":
        thumb_img = "thumbnail.jpg"
        download_file(file_id, thumb_img)
        
        title = "Viral Must-Watch Video Highlight"
        description = "Enjoy this video. Like and subscribe for more content!\n\n#viral #trending"
        tags = ["viral", "trending", "video", "highlights"]
        upload_to_youtube(raw_video, title, description, tags, thumbnail_path=thumb_img)
        
    elif mode == "short":
        short_video = "short_clip.mp4"
        start_time = random.randint(0, 30)
        
        cmd = [
            "ffmpeg", "-y", "-ss", str(start_time), "-t", "45",
            "-i", raw_video,
            "-vf", "crop=ih*(9/16):ih,scale=1080:1920",
            "-c:a", "copy",
            short_file
        ]
        subprocess.run(cmd, check=True)
        
        title = "Amazing Moment #Shorts"
        description = "Enjoy this short clip. #Shorts #viral #trending"
        tags = ["shorts", "viral", "trending"]
        upload_to_youtube(short_video, title, description, tags)

if __name__ == "__main__":
    run()
