import aiohttp
from core.config import config


class CryptoPayService:
    BASE_URL = config.crypto_pay_url

    def __init__(self):
        self.headers = {"Crypto-Pay-API-Token": config.crypto_pay_token}

    async def create_invoice(
        self,
        amount: float,
        description: str,
        payload: str,
    ) -> dict:
        """Создаёт инвойс в CryptoBot, возвращает dict с pay_url и invoice_id."""
        params = {
            "currency_type": "fiat",
            "fiat": "USD",
            "accepted_assets": "USDT,TON,BTC,ETH",
            "amount": str(amount),
            "description": description,
            "payload": payload,
            "paid_btn_name": "callback",
            "paid_btn_url": f"https://t.me/{(await self._get_bot_username())}",
        }
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(f"{self.BASE_URL}/createInvoice", json=params) as resp:
                data = await resp.json()

        if not data.get("ok"):
            raise RuntimeError(f"CryptoPay error: {data}")

        return data["result"]  # .pay_url, .invoice_id

    async def get_invoice(self, invoice_ids: list[str]) -> list[dict]:
        params = {"invoice_ids": ",".join(invoice_ids)}
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(f"{self.BASE_URL}/getInvoices", params=params) as resp:
                data = await resp.json()
        return data.get("result", {}).get("items", [])

    async def _get_bot_username(self) -> str:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(f"{self.BASE_URL}/getMe") as resp:
                data = await resp.json()
        return data["result"].get("name", "bot")


crypto_pay = CryptoPayService()