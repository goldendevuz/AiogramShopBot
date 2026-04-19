"""
UZS → USD konvertatsiya yordamchisi.
Redis mavjud bo'lsa — kursni 1 soat cache qiladi (API limitini tejaydi).
Redis yo'q bo'lsa — har safar API dan oladi.

Manba: https://open.er-api.com  (1500 so'rov/oy bepul, API key shart emas)
"""

import httpx

EXCHANGE_API_URL = "https://open.er-api.com/v6/latest/USD"
CACHE_KEY = "uzs_usd_rate"
CACHE_TTL = 21600  # 6 soat (sekundda), 1 soat - 3600 sekund


async def get_uzs_per_usd(redis=None) -> float:
    """
    1 USD = necha UZS ekanini qaytaradi.
    Masalan: 12142.7
    """
    # 1. Redisdan olishga urinish
    if redis:
        try:
            cached = await redis.get(CACHE_KEY)
            if cached:
                return float(cached)
        except Exception:
            pass  # Redis xatosi bo'lsa — APIdan olamiz

    # 2. APIdan olish
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(EXCHANGE_API_URL)
        response.raise_for_status()
        data = response.json()
        rate: float = data["rates"]["UZS"]

    # 3. Redisga saqlash
    if redis:
        try:
            await redis.setex(CACHE_KEY, CACHE_TTL, str(rate))
        except Exception:
            pass

    return rate


async def uzs_to_usd(amount_uzs: float, redis=None) -> float:
    """
    UZS miqdorini USD ga o'giradi.
    Masalan: 100_000 UZS → ~8.23 USD
    """
    rate = await get_uzs_per_usd(redis)
    return round(amount_uzs / rate, 2)


async def usd_to_uzs(amount_usd: float, redis=None) -> float:
    """
    USD miqdorini UZS ga o'giradi.
    Masalan: 8.23 USD → ~100_000 UZS
    """
    rate = await get_uzs_per_usd(redis)
    return round(amount_usd * rate, 2)
