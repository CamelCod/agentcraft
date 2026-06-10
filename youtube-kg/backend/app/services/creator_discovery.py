"""
Discovers YouTube channel metadata and video list using the YouTube Data API v3.
Accepts channel URLs in any format: /channel/ID, /c/handle, /@handle, /user/name.
"""
import re
from dataclasses import dataclass
from datetime import datetime

import httpx
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import get_settings

settings = get_settings()


@dataclass
class ChannelMeta:
    channel_id: str
    channel_name: str
    channel_url: str
    description: str
    subscriber_count: int | None
    video_count: int | None
    thumbnail_url: str | None
    country: str | None
    raw: dict


@dataclass
class VideoMeta:
    youtube_id: str
    title: str
    description: str
    tags: list[str]
    duration_seconds: int | None
    published_at: datetime | None
    thumbnail_url: str | None
    view_count: int | None


def _build_service():
    return build("youtube", "v3", developerKey=settings.youtube_api_key, cache_discovery=False)


def _resolve_channel_id(url: str) -> str:
    """Return channel_id from any YouTube channel URL format."""
    service = _build_service()

    # Direct /channel/UCxxx format
    m = re.search(r"/channel/(UC[\w-]{22})", url)
    if m:
        return m.group(1)

    # @handle or /c/handle or /user/name
    handle_match = re.search(r"/@([\w.-]+)|/c/([\w.-]+)|/user/([\w.-]+)", url)
    if handle_match:
        handle = next(g for g in handle_match.groups() if g)
        resp = (
            service.channels()
            .list(part="id", forHandle=handle)
            .execute()
        )
        items = resp.get("items", [])
        if items:
            return items[0]["id"]
        # Fall back to search
        resp = service.search().list(part="snippet", q=handle, type="channel", maxResults=1).execute()
        items = resp.get("items", [])
        if items:
            return items[0]["snippet"]["channelId"]

    raise ValueError(f"Cannot resolve channel ID from URL: {url}")


def discover_channel(creator_url: str) -> ChannelMeta:
    service = _build_service()
    channel_id = _resolve_channel_id(creator_url)

    resp = service.channels().list(
        part="snippet,statistics,brandingSettings",
        id=channel_id,
    ).execute()

    items = resp.get("items", [])
    if not items:
        raise ValueError(f"Channel not found: {channel_id}")

    ch = items[0]
    snippet = ch.get("snippet", {})
    stats = ch.get("statistics", {})

    return ChannelMeta(
        channel_id=channel_id,
        channel_name=snippet.get("title", ""),
        channel_url=f"https://www.youtube.com/channel/{channel_id}",
        description=snippet.get("description", ""),
        subscriber_count=int(stats["subscriberCount"]) if stats.get("subscriberCount") else None,
        video_count=int(stats["videoCount"]) if stats.get("videoCount") else None,
        thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url"),
        country=snippet.get("country"),
        raw=ch,
    )


def discover_videos(channel_id: str, max_results: int = 500) -> list[VideoMeta]:
    """Returns up to max_results videos from a channel, oldest-first."""
    service = _build_service()
    videos: list[VideoMeta] = []
    page_token = None

    # Get uploads playlist ID
    resp = service.channels().list(part="contentDetails", id=channel_id).execute()
    uploads_playlist = (
        resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    )

    while len(videos) < max_results:
        kwargs = dict(
            part="snippet",
            playlistId=uploads_playlist,
            maxResults=min(50, max_results - len(videos)),
        )
        if page_token:
            kwargs["pageToken"] = page_token

        resp = service.playlistItems().list(**kwargs).execute()
        video_ids = [
            item["snippet"]["resourceId"]["videoId"]
            for item in resp.get("items", [])
        ]

        # Fetch video details in batch
        detail_resp = service.videos().list(
            part="snippet,contentDetails,statistics",
            id=",".join(video_ids),
        ).execute()

        for v in detail_resp.get("items", []):
            snippet = v["snippet"]
            stats = v.get("statistics", {})
            duration_raw = v.get("contentDetails", {}).get("duration", "")
            duration_secs = _parse_iso8601_duration(duration_raw)
            published_str = snippet.get("publishedAt")
            published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00")) if published_str else None

            videos.append(VideoMeta(
                youtube_id=v["id"],
                title=snippet.get("title", ""),
                description=snippet.get("description", ""),
                tags=snippet.get("tags", []),
                duration_seconds=duration_secs,
                published_at=published_at,
                thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url"),
                view_count=int(stats["viewCount"]) if stats.get("viewCount") else None,
            ))

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return videos


def _parse_iso8601_duration(duration: str) -> int | None:
    """Convert PT#H#M#S to seconds."""
    if not duration:
        return None
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if not m:
        return None
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + s
