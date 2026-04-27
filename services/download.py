import re
import httpx
import asyncio
import tempfile

from config import API_URL, API_KEY


# =========================
# HTTP CLIENT (PRODUCTION SAFE)
# =========================
client = httpx.AsyncClient(
    base_url=API_URL,
    timeout=httpx.Timeout(
        connect=10.0,
        read=600.0,
        write=10.0,
        pool=10.0
    ),
    limits=httpx.Limits(
        max_connections=50,
        max_keepalive_connections=20
    ),
)


# =========================
# URL DETECTOR (YOUTUBE vs OTHER)
# =========================
def is_youtube(url: str) -> bool:
    return bool(re.search(r"(youtube\.com|youtu\.be)", url))


def build_caption(url: str) -> str:
    return (
        "📥 <b>Video muvaffaqiyatli yuklab olindi</b>\n"
        f"🔗 <a href='{url}'>Asl havola</a>\n"
        "⚡ <a href='https://t.me/secondsaverbot'>FastSaver Bot</a>"
    )


# =========================
# YOUTUBE DOWNLOAD (NEW ENDPOINT)
# =========================
async def fetch_youtube(url: str, retries: int = 2):
    for attempt in range(retries):
        try:
            response = await client.post(
                "/youtube/download",
                headers={
                    "X-Api-Key": API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "url": url,
                    "format": "1080p"
                }
            )

            if response.status_code == 429:
                await asyncio.sleep(2 + attempt)
                continue

            if response.status_code >= 500:
                await asyncio.sleep(1 + attempt)
                continue

            if response.status_code != 200:
                return {"error": "YouTube API xatolik"}

            data = response.json()

            if not isinstance(data, dict) or not data.get("ok"):
                return {"error": "YouTube video topilmadi"}

            download_url = data.get("download_url")

            if not download_url:
                return {"error": "YouTube yuklab olish havolasi yo‘q"}

            return {
                "video_url": download_url,
                "caption": build_caption(url)
            }

        except httpx.TimeoutException:
            await asyncio.sleep(1.5 + attempt)

        except Exception:
            await asyncio.sleep(1)

    return {"error": "YouTube yuklab bo‘lmadi"}


# =========================
# GENERIC FETCH (OTHER PLATFORMS)
# =========================
async def fetch_generic(url: str, retries: int = 3):
    for attempt in range(retries):
        try:
            response = await client.get(
                "/fetch",
                params={"url": url},
                headers={"X-Api-Key": API_KEY},
            )

            if response.status_code == 429:
                await asyncio.sleep(2 + attempt)
                continue

            if response.status_code >= 500:
                await asyncio.sleep(1 + attempt)
                continue

            if response.status_code != 200:
                return {"error": "API error"}

            data = response.json()

            if not isinstance(data, dict) or not data.get("ok"):
                return {"error": "Video topilmadi"}

            download_url = data.get("download_url")

            if not download_url:
                return {"error": "Download URL yo‘q"}

            return {
                "video_url": download_url,
                "caption": build_caption(url)
            }

        except httpx.TimeoutException:
            await asyncio.sleep(1.5 + attempt)

        except Exception:
            await asyncio.sleep(1)

    return {"error": "Yuklab bo‘lmadi"}


# =========================
# MAIN ENTRY POINT (SINGLE FUNCTION)
# =========================
async def fetch_download_data(url: str):
    try:
        # =========================
        # YOUTUBE ROUTE
        # =========================
        if is_youtube(url):
            return await fetch_youtube(url)

        # =========================
        # OTHER PLATFORMS ROUTE
        # =========================
        return await fetch_generic(url)

    except Exception as e:
        return {"error": str(e)}


async def download_file(url: str) -> str:
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    temp_path = temp_file.name

    async with client.stream("GET", url) as response:
        response.raise_for_status()

        with open(temp_path, "wb") as f:
            async for chunk in response.aiter_bytes():
                f.write(chunk)

    return temp_path
