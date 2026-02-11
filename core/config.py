from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv
import os

load_dotenv()


@dataclass
class Channel:
    username: str
    name: str


@dataclass
class Tariff:
    id: str
    label: str
    price_usd: float
    months: int = 0
    days: int = 0
    hours: int = 0
    is_infinite: bool = False


TARIFFS: List[Tariff] = [
    Tariff(id="10h",  label="10 часов",  price_usd=0.17, hours=10),
    Tariff(id="1d",   label="1 день",    price_usd=0.28, days=1),
    Tariff(id="7d",   label="7 дней",    price_usd=0.39, days=7),
    Tariff(id="14d",  label="14 дней",   price_usd=0.50, days=14),
    Tariff(id="30d",  label="30 дней",   price_usd=0.61, days=30),
    Tariff(id="60d",  label="60 дней",   price_usd=0.72, days=60),
    Tariff(id="inf",  label="Навсегда",  price_usd=0.83, is_infinite=True),
]


@dataclass
class Config:
    bot_token: str
    channels: List[Channel]
    crypto_pay_token: str
    crypto_pay_url: str
    mod_channel_link: str
    private_channel_id: int
    license_key: str
    database_url: str
    admin_ids: List[int]
    tariffs: List[Tariff] = field(default_factory=lambda: TARIFFS)


def load_config() -> Config:
    def require(key: str) -> str:
        val = os.getenv(key)
        if not val:
            raise ValueError(f"{key} не задан в .env")
        return val

    raw_channels = os.getenv("REQUIRED_CHANNELS", "")
    raw_names = os.getenv("CHANNEL_NAMES", "")
    usernames = [c.strip() for c in raw_channels.split(",") if c.strip()]
    names = [n.strip() for n in raw_names.split(",") if n.strip()]
    channels = [
        Channel(username=u, name=names[i] if i < len(names) else u)
        for i, u in enumerate(usernames)
    ]

    raw_admins = os.getenv("ADMIN_IDS", "")
    admin_ids = [int(a.strip()) for a in raw_admins.split(",") if a.strip().isdigit()]

    raw_channel_id = os.getenv("PRIVATE_CHANNEL_ID", "0")
    private_channel_id = int(raw_channel_id) if raw_channel_id.lstrip("-").isdigit() else 0

    return Config(
        bot_token=require("BOT_TOKEN"),
        channels=channels,
        crypto_pay_token=require("CRYPTO_PAY_TOKEN"),
        crypto_pay_url=os.getenv("CRYPTO_PAY_URL", "https://pay.crypt.bot/api"),
        mod_channel_link=os.getenv("MOD_CHANNEL_LINK", ""),
        private_channel_id=private_channel_id,
        license_key=require("LICENSE_KEY"),
        database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db"),
        admin_ids=admin_ids,
        tariffs=TARIFFS,
    )


config = load_config()