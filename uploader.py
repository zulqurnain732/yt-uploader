import os
import re
import json
import random
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("REFRESH_TOKEN")
GDRIVE_API_KEY = os.environ.get("GDRIVE_API_KEY")

TRACKER_FILE = "uploaded.json"
FOLDER_ID = "1nbXalCCa3umvQmrhzRogjvnSz-zMYfHj"

creds = Credentials(
    None,
    refresh_token=REFRESH_TOKEN,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
)
youtube_service = build('youtube', 'v3', credentials=creds)
drive_service = build('drive', 'v3', developerKey=GDRIVE_API_KEY)

if os.path.exists(TRACKER_FILE):
    try:
        with open(TRACKER_FILE, "r") as f:
            uploaded_files = set(json.load(f))
    except Exception:
        uploaded_files = set()
else:
    uploaded_files = set()

print("Fetching folder items via Google Drive API...")
query = f"'{FOLDER_ID}' in parents and trashed = false"
response = drive_service.files().list(
    q=query,
    pageSize=100,
    fields="files(id, name, mimeType, shortcutDetails)"
).execute()

items = response.get('files', [])
ignored_names = ["1m $ earning", "400  free reels bundle", "4000 free courses"]

def extract_number(filename):
    nums = re.findall(r'\d+', filename)
    return int(nums[0]) if nums else 999999

valid_videos = []
for item in items:
    name = item.get('name', '')
    lower_name = name.lower()
    if any(ign in lower_name for ign in ignored_names):
        continue

    if item.get('mimeType') == 'application/vnd.google-apps.shortcut':
        shortcut_details = item.get('shortcutDetails', {})
        target_id = shortcut_details.get('targetId')
        target_mime = shortcut_details.get('targetMimeType', '')
        if target_id and ('video' in target_mime or name.endswith('.mp4')):
            valid_videos.append({'name': name, 'id': target_id})
    elif 'video' in item.get('mimeType', '') or name.endswith('.mp4'):
        valid_videos.append({'name': name, 'id': item['id']})

valid_videos.sort(key=lambda x: extract_number(x['name']))
pending_videos = [v for v in valid_videos if v['name'] not in uploaded_files]

print(f"Total video shortcuts found: {len(valid_videos)}")
print(f"Pending to upload: {len(pending_videos)}")

if not pending_videos:
    print("Koi nayi video pending nahi hai!")
    exit(0)

target = pending_videos[0]
target_name = target['name']
target_id = target['id']

print(f"\nTarget Video Selected: {target_name} (Resolved File ID: {target_id})")

local_video_file = "video_to_upload.mp4"
print("Downloading video stream...")

download_url = f"https://www.googleapis.com/drive/v3/files/{target_id}?alt=media&key={GDRIVE_API_KEY}"
with requests.get(download_url, stream=True) as r:
    r.raise_for_status()
    with open(local_video_file, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)

file_size_mb = os.path.getsize(local_video_file) / (1024 * 1024)
print(f"Downloaded successfully! File size: {file_size_mb:.2f} MB")

roblox_titles = [
    "Most Insane Roblox Moment! 😱 #roblox #shorts",
    "Only 1% Can Beat This Roblox Obby! 🔥 #roblox #shorts",
    "Roblox Funniest Gameplay Ever 😂 #roblox #shorts",
    "You Won't Believe What Happened in Roblox! 🤯 #roblox #shorts",
    "Crazy Roblox Glitch You Must Try! 🎮 #roblox #shorts",
    "Roblox Pro vs Noob Moment 💀 #roblox #shorts",
    "Top Secret Roblox Trick Revealed! ⚡ #roblox #shorts",
    "Roblox Impossible Challenge Cleared! 🏆 #roblox #shorts",
    "Best Roblox Avatar & Animation! ✨ #roblox #shorts",
    "Roblox Chaos at its Peak! 🚀 #roblox #shorts"
]

description_text = """Check out this epic Roblox gameplay! 🎮
Subscribe for more daily Roblox Shorts and gaming moments.

#roblox #robloxshorts #gaming #robloxtrend #shorts #viral"""

tags_list = ["roblox", "roblox shorts", "roblox funny moments", "gaming", "shorts", "roblox gameplay", "trending"]

title = random.choice(roblox_titles)
body = {
    'snippet': {
        'title': title,
        'description': description_text,
        'tags': tags_list,
        'categoryId': '20'
    },
    'status': {
        'privacyStatus': 'public'
    }
}

print(f"YouTube par upload jaari hai: {title}")
media = MediaFileUpload(local_video_file, chunksize=-1, resumable=True, mimetype='video/mp4')
response = youtube_service.videos().insert(
    part=','.join(body.keys()),
    body=body,
    media_body=media
).execute()

print(f"Success! Video Uploaded successfully. ID: {response.get('id')}")

uploaded_files.add(target_name)
with open(TRACKER_FILE, "w") as f:
    json.dump(list(uploaded_files), f, indent=2)

if os.path.exists(local_video_file):
    os.remove(local_video_file)
