import re

import httpx


SHORT_LINK_RE = re.compile(r"https?://v\.douyin\.com/[A-Za-z0-9\-_]+/?", re.IGNORECASE)
LIVE_ROOM_RE = re.compile(r"https?://live\.douyin\.com/(\d+)", re.IGNORECASE)
WEB_RID_RE = re.compile(r'"webRid"\s*:\s*"(\d+)"')


class DouyinNormalizationError(ValueError):
    """Raised when Douyin input cannot be normalized into a live room URL."""


def extract_douyin_candidate_url(raw_text: str) -> str | None:
    live_match = LIVE_ROOM_RE.search(raw_text)
    if live_match:
        return f"https://live.douyin.com/{live_match.group(1)}"

    short_match = SHORT_LINK_RE.search(raw_text)
    if short_match:
        return short_match.group(0)

    return None


async def normalize_douyin_input(raw_text: str, proxy: str | None = None, timeout: float = 10.0) -> str:
    candidate_url = extract_douyin_candidate_url(raw_text.strip())
    if not candidate_url:
        raise DouyinNormalizationError("No Douyin URL found in input")

    live_match = LIVE_ROOM_RE.fullmatch(candidate_url)
    if live_match:
        return f"https://live.douyin.com/{live_match.group(1)}"

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            proxy=proxy,
            timeout=timeout,
        ) as client:
            response = await client.get(candidate_url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise DouyinNormalizationError("Failed to resolve Douyin share link") from exc

    web_rid_match = WEB_RID_RE.search(response.text)
    if not web_rid_match:
        raise DouyinNormalizationError("Failed to extract Douyin live room id")

    return f"https://live.douyin.com/{web_rid_match.group(1)}"
