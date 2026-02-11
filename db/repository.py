from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from db.models import User, Subscription, Payment, GateChannel, ModChannel
from datetime import datetime, timedelta
from typing import Optional


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[User]:
        result = await self.session.execute(select(User))
        return list(result.scalars().all())

    async def get_or_create(self, telegram_id: int, full_name: str, username: str | None) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            user = User(telegram_id=telegram_id, full_name=full_name, username=username)
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
        return user


class SubscriptionRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active(self, user_id: int) -> Optional[Subscription]:
        result = await self.session.execute(
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.is_active == True,
                Subscription.expires_at > datetime.utcnow()
            )
            .order_by(Subscription.expires_at.desc())
        )
        return result.scalar_one_or_none()

    async def get_all(self, user_id: int) -> list[Subscription]:
        result = await self.session.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.started_at.desc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        user_id: int,
        tariff_id: str,
        months: int = 0,
        days: int = 0,
        hours: int = 0,
        is_infinite: bool = False
    ) -> Subscription:
        active = await self.get_active(user_id)
        start = active.expires_at if active else datetime.utcnow()

        if is_infinite:
            expires = datetime(9999, 12, 31)
        else:
            expires = start + timedelta(days=days, hours=hours) + timedelta(days=30 * months)

        sub = Subscription(
            user_id=user_id,
            tariff_id=tariff_id,
            started_at=datetime.utcnow(),
            expires_at=expires,
        )
        self.session.add(sub)
        await self.session.commit()
        await self.session.refresh(sub)
        return sub


class PaymentRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, invoice_id: str, tariff_id: str, amount: float) -> Payment:
        payment = Payment(
            user_id=user_id,
            invoice_id=invoice_id,
            tariff_id=tariff_id,
            amount_usd=amount,
        )
        self.session.add(payment)
        await self.session.commit()
        await self.session.refresh(payment)
        return payment

    async def get_by_invoice(self, invoice_id: str) -> Optional[Payment]:
        result = await self.session.execute(
            select(Payment).where(Payment.invoice_id == invoice_id)
        )
        return result.scalar_one_or_none()

    async def mark_paid(self, invoice_id: str) -> None:
        await self.session.execute(
            update(Payment)
            .where(Payment.invoice_id == invoice_id)
            .values(is_paid=True)
        )
        await self.session.commit()


class GateChannelRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[GateChannel]:
        result = await self.session.execute(
            select(GateChannel).order_by(GateChannel.added_at)
        )
        return list(result.scalars().all())

    async def add(self, username: str, title: str) -> GateChannel:
        channel = GateChannel(username=username, title=title)
        self.session.add(channel)
        await self.session.commit()
        await self.session.refresh(channel)
        return channel

    async def remove(self, channel_id: int) -> None:
        await self.session.execute(
            delete(GateChannel).where(GateChannel.id == channel_id)
        )
        await self.session.commit()

    async def count(self) -> int:
        channels = await self.get_all()
        return len(channels)


class ModChannelRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[ModChannel]:
        result = await self.session.execute(
            select(ModChannel).order_by(ModChannel.added_at)
        )
        return list(result.scalars().all())

    async def get_private_channels(self) -> list[ModChannel]:
        result = await self.session.execute(
            select(ModChannel).where(ModChannel.is_private == True)
        )
        return list(result.scalars().all())

    async def add(
        self,
        username: str,
        title: str,
        url: str,
        is_private: bool = False,
        channel_id: int | None = None
    ) -> ModChannel:
        channel = ModChannel(
            username=username,
            title=title,
            url=url,
            is_private=is_private,
            channel_id=channel_id
        )
        self.session.add(channel)
        await self.session.commit()
        await self.session.refresh(channel)
        return channel

    async def remove(self, channel_id: int) -> None:
        await self.session.execute(
            delete(ModChannel).where(ModChannel.id == channel_id)
        )
        await self.session.commit()

    async def count(self) -> int:
        channels = await self.get_all()
        return len(channels)