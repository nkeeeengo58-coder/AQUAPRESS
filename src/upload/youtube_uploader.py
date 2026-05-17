"""YouTube uploader for AQUA PRESS videos."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except ImportError:
    # Graceful degradation if google libraries not installed
    pass


SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CREDENTIALS_FILE = "youtube_credentials.json"
TOKEN_FILE = "youtube_token.json"


def _get_credentials() -> Optional[Credentials]:
    """Get YouTube API credentials with OAuth2 flow."""
    token_path = Path(TOKEN_FILE)
    credentials_path = Path(CREDENTIALS_FILE)

    # Try to load existing token
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        if creds and creds.valid:
            return creds
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_path.write_text(creds.to_json())
            return creds

    # If no valid token, create new OAuth flow
    if not credentials_path.exists():
        print("[ERROR] youtube_credentials.json not found")
        print("[INFO] Download from: https://console.cloud.google.com/apis/credentials")
        return None

    try:
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())
        return creds
    except Exception as exc:
        print(f"[ERROR] OAuth flow failed: {exc}")
        return None


def upload_video(
    video_path: str | Path,
    title: str,
    description: str = "",
    tags: list[str] | None = None,
    thumbnail_path: str | Path | None = None,
    privacy_status: str = "private",
    playlist_id: str | None = None,
) -> Optional[str]:
    """
    Upload video to YouTube.

    Args:
        video_path: Path to video file
        title: Video title
        description: Video description
        tags: List of tags/keywords
        thumbnail_path: Path to custom thumbnail
        privacy_status: 'public', 'unlisted', or 'private'
        playlist_id: Optional playlist ID to add video to

    Returns:
        Video ID if successful, None otherwise
    """
    video_file = Path(video_path)
    if not video_file.exists():
        print(f"[ERROR] Video file not found: {video_path}")
        return None

    creds = _get_credentials()
    if not creds:
        print("[ERROR] Failed to get YouTube credentials")
        return None

    try:
        youtube = build("youtube", "v3", credentials=creds)

        # Prepare video metadata
        body = {
            "snippet": {
                "title": title[:100],  # YouTube title limit: 100 chars
                "description": description[:5000],  # YouTube description limit: 5000 chars
                "tags": tags[:30] if tags else [],  # YouTube tag limit: 30
                "categoryId": "26",  # Category 26 = Animals
                "defaultLanguage": "ja",
                "defaultAudioLanguage": "ja",
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        # Upload video with resumable upload (for large files)
        media = MediaFileUpload(
            str(video_file),
            mimetype="video/mp4",
            resumable=True,
            chunksize=10 * 1024 * 1024,  # 10MB chunks
        )

        print(f"[INFO] Uploading video to YouTube: {title[:50]}...")
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

        response = None
        while response is None:
            try:
                status, response = request.next_chunk()
                if status:
                    print(f"[INFO] Upload progress: {int(status.progress() * 100)}%")
            except Exception as exc:
                print(f"[ERROR] Upload failed: {exc}")
                return None

        video_id = response.get("id")
        print(f"[OK] Video uploaded: https://youtube.com/watch?v={video_id}")

        # Upload thumbnail if provided
        if thumbnail_path:
            try:
                thumb_file = Path(thumbnail_path)
                if thumb_file.exists():
                    youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(str(thumb_file))).execute()
                    print(f"[INFO] Thumbnail uploaded")
            except Exception as exc:
                print(f"[WARN] Thumbnail upload failed: {exc}")

        # Add to playlist if specified
        if playlist_id:
            try:
                youtube.playlistItems().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "playlistId": playlist_id,
                            "resourceId": {"kind": "youtube#video", "videoId": video_id},
                        }
                    },
                ).execute()
                print(f"[INFO] Added to playlist: {playlist_id}")
            except Exception as exc:
                print(f"[WARN] Playlist add failed: {exc}")

        return video_id

    except Exception as exc:
        print(f"[ERROR] YouTube API error: {exc}")
        return None


def get_upload_status(video_id: str) -> Optional[dict]:
    """Get video upload/processing status."""
    creds = _get_credentials()
    if not creds:
        return None

    try:
        youtube = build("youtube", "v3", credentials=creds)
        response = youtube.videos().list(part="status,processingDetails", id=video_id).execute()

        if response.get("items"):
            item = response["items"][0]
            return {
                "privacy_status": item.get("status", {}).get("privacyStatus"),
                "upload_status": item.get("status", {}).get("uploadStatus"),
                "processing_status": item.get("processingDetails", {}).get("processingStatus"),
                "processing_progress": item.get("processingDetails", {}).get("processingProgress"),
            }
    except Exception as exc:
        print(f"[ERROR] Failed to get status: {exc}")

    return None
