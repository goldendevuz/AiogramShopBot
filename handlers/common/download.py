import asyncio
import logging
import tempfile
import os

from aiogram import Router, F, Bot
from aiogram.types import Message, FSInputFile

from services.download import fetch_download_data, download_file
from enums.links import Links

download_router = Router()

async def safe_reply(bot: Bot, message: Message, text: str):
    return await bot.send_message(
        chat_id=message.chat.id,
        text=text
    )


# =========================
# FIXED VIDEO SENDER
# =========================
async def safe_send_video(bot: Bot, message: Message, url: str, caption: str):
    chat_id = message.chat.id

    logging.info(f"📥 DOWNLOADING VIDEO: {url}")

    try:
        # 1. DOWNLOAD FILE LOCALLY
        file_path = await download_file(url)

        video = FSInputFile(file_path)

        # 2. SEND AS VIDEO
        await bot.send_video(
            chat_id=chat_id,
            video=video,
            caption=caption,
            supports_streaming=True
        )

        # 3. CLEANUP
        os.remove(file_path)

    except Exception as e:
        logging.warning(f"send_video failed: {e}")

        try:
            # fallback as document
            file_path = await download_file(url)

            doc = FSInputFile(file_path)

            await bot.send_document(
                chat_id=chat_id,
                document=doc,
                caption=caption
            )

            os.remove(file_path)

        except Exception as e2:
            logging.error(f"send_document failed: {e2}")

            await bot.send_message(
                chat_id=chat_id,
                text=f"❌ Xatolik: {str(e2)}"
            )


# =========================
# LOADING UX
# =========================
FRAMES = [
    "⏳ Yuklanmoqda...",
    "⏳ Yuklanmoqda ▰▱▱▱",
    "⏳ Yuklanmoqda ▰▰▱▱",
    "⏳ Yuklanmoqda ▰▰▰▱",
    "⏳ Yuklanmoqda ▰▰▰▰",
]


async def loading_loop(bot: Bot, chat_id: int, message_id: int, stop: asyncio.Event):
    i = 0
    while not stop.is_set():
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=FRAMES[i % len(FRAMES)]
            )
        except Exception:
            pass

        i += 1
        await asyncio.sleep(0.5)


# =========================
# CORE
# =========================
async def process_download(message: Message, bot: Bot):
    chat_id = message.chat.id
    text = (message.text or "").strip()
    caption=f"<b><i><a href='https://t.me/secondsaverbot'>@secondsaverbot</a> | <a href='{text}'>link</a> | <a href='https://l.rhmt.uz/BTZs72'>donate</a></i></b>"

    msg = await safe_reply(bot, message, "⏳ Boshlanmoqda...")

    stop = asyncio.Event()
    loader = asyncio.create_task(
        loading_loop(bot, chat_id, msg.message_id, stop)
    )

    try:
        data = await fetch_download_data(text)

        stop.set()
        await loader

        if not data or data.get("error"):
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg.message_id,
                text="❌ Video topilmadi"
            )
            return

        video_url = data.get("video_url")

        if not video_url:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg.message_id,
                text="❌ URL yo‘q"
            )
            return

        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg.message_id,
            text="📥 Yuklab olinmoqda..."
        )

        await safe_send_video(
            bot,
            message,
            video_url,
            caption=caption
        )

        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg.message_id,
            text="🎉 Tayyor!"
        )

    except Exception as e:
        stop.set()
        await loader

        logging.error(f"CRITICAL ERROR: {e}")

        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg.message_id,
            text="💥 Xatolik yuz berdi"
        )


@download_router.message()
async def download_private(message: Message, bot: Bot):
    await process_download(message, bot)

