from decouple import config, Csv

from enums.currency import Currency
from enums.runtime_environment import RuntimeEnvironment
from utils.utils import get_sslipio_external_url, start_ngrok, hash_password

# CORE ENV
RUNTIME_ENVIRONMENT = RuntimeEnvironment(config("RUNTIME_ENVIRONMENT"))

if RUNTIME_ENVIRONMENT == RuntimeEnvironment.DEV:
    WEBHOOK_HOST = start_ngrok()
else:
    WEBHOOK_HOST = get_sslipio_external_url()

WEBHOOK_PATH = config("WEBHOOK_PATH", default="/")
WEBAPP_HOST = config("WEBAPP_HOST", default="0.0.0.0")
WEBAPP_PORT = config("WEBAPP_PORT", default=5000, cast=int)

WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

TOKEN = config("TOKEN")

ADMIN_ID_LIST = config("ADMIN_ID_LIST", cast=Csv(int))

SUPPORT_LINK = config("SUPPORT_LINK", default=None)

# POSTGRESQL
DB_USER = config("POSTGRES_USER", default="postgres")
DB_PASS = config("POSTGRES_PASSWORD")
DB_PORT = config("DB_PORT", default=5432, cast=int)
DB_HOST = config("DB_HOST", default="postgres")
DB_NAME = config("POSTGRES_DB", default="aiogram-shop-bot")

PAGE_ENTRIES = config("PAGE_ENTRIES", default=8, cast=int)

MULTIBOT = config("MULTIBOT", default=False, cast=bool)

CURRENCY = Currency(config("CURRENCY", default="UZS"))

# KRYPTO EXPRESS
KRYPTO_EXPRESS_API_KEY = config("KRYPTO_EXPRESS_API_KEY", default=None)
KRYPTO_EXPRESS_API_URL = config("KRYPTO_EXPRESS_API_URL", default=None)
KRYPTO_EXPRESS_API_SECRET = config("KRYPTO_EXPRESS_API_SECRET", default=None)

WEBHOOK_SECRET_TOKEN = config("WEBHOOK_SECRET_TOKEN", default=None)

# REDIS
REDIS_HOST = config("REDIS_HOST", default="redis")
REDIS_PASSWORD = config("REDIS_PASSWORD", default=None)

TELEGRAM_PROXY_URL = config("TELEGRAM_PROXY_URL", default=None)

# CRYPTO FORWARDING
CRYPTO_FORWARDING_MODE = config("CRYPTO_FORWARDING_MODE", default=False, cast=bool)

BTC_FORWARDING_ADDRESS = config("BTC_FORWARDING_ADDRESS", default=None)
LTC_FORWARDING_ADDRESS = config("LTC_FORWARDING_ADDRESS", default=None)
ETH_FORWARDING_ADDRESS = config("ETH_FORWARDING_ADDRESS", default=None)
SOL_FORWARDING_ADDRESS = config("SOL_FORWARDING_ADDRESS", default=None)
BNB_FORWARDING_ADDRESS = config("BNB_FORWARDING_ADDRESS", default=None)
DOGE_FORWARDING_ADDRESS = config("DOGE_FORWARDING_ADDRESS", default=None)

# REFERRAL SYSTEM
MIN_REFERRER_TOTAL_DEPOSIT = config("MIN_REFERRER_TOTAL_DEPOSIT", default=500, cast=int)

REFERRAL_BONUS_PERCENT = config("REFERRAL_BONUS_PERCENT", default=5, cast=float)
REFERRAL_BONUS_DEPOSIT_LIMIT = config("REFERRAL_BONUS_DEPOSIT_LIMIT", default=3, cast=int)

REFERRER_BONUS_PERCENT = config("REFERRER_BONUS_PERCENT", default=3, cast=float)
REFERRER_BONUS_DEPOSIT_LIMIT = config("REFERRER_BONUS_DEPOSIT_LIMIT", default=5, cast=int)

REFERRAL_BONUS_CAP_PERCENT = config("REFERRAL_BONUS_CAP_PERCENT", default=7, cast=float)
REFERRER_BONUS_CAP_PERCENT = config("REFERRER_BONUS_CAP_PERCENT", default=7, cast=float)
TOTAL_BONUS_CAP_PERCENT = config("TOTAL_BONUS_CAP_PERCENT", default=12, cast=float)

# SQLADMIN
SQLADMIN_RAW_PASSWORD = config("SQLADMIN_RAW_PASSWORD")
SQLADMIN_HASHED_PASSWORD = hash_password(SQLADMIN_RAW_PASSWORD)

# JWT
JWT_EXPIRE_MINUTES = config("JWT_EXPIRE_MINUTES", default=30, cast=int)
JWT_ALGORITHM = config("JWT_ALGORITHM", default="HS256")
JWT_SECRET_KEY = config("JWT_SECRET_KEY")

# DOWNLOAD SERVICE
API_URL = config("API_URL", default="https://api.univel.uz")
API_KEY = config("API_KEY", default="d8137404-8685-4182-89b8-11c6a71ab548")
