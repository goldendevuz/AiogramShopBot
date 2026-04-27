from enum import Enum


class MediaStatusMessages(str, Enum):
    VideoProcessing = "⏳ Your video is being processed..."
    VideoSuccess = "✅ Your video has been successfully downloaded. Sending..."
    VideoNotSent = "❌ Unfortunately, the video exceeds Telegram limits."
    VideoError = "⚠️ An error occurred during the download."
