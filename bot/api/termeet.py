import aiohttp
from bot.config import config


class TermeetClient:
    def __init__(self):
        self.base_url = config.BACKEND_API_URL.rstrip("/")

    async def create_meeting(
        self,
        name: str,
        data_range: list,
        description: str | None = None,
        duration: str | None = None,
        link: str | None = None,
    ) -> dict:
        payload: dict = {"name": name, "data_range": data_range}

        if description:
            payload["description"] = description
        if duration:
            payload["duration"] = duration
        if link:
            payload["link"] = link

        # Здесь заменить на RabbitMQ + retry-и
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/meet/create", json=payload
            ) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def get_meeting(self, hash: str) -> dict | None:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/meet/{hash}") as resp:
                if resp.status == 404:
                    return None
                resp.raise_for_status()
                return await resp.json()

    # Здесь продумать логику с редактированием слотов на ручку .\...\slots\edit
    async def update_slots(self, hash: str, name: str, slots: list) -> dict:

        payload = {"name": name, "slots": slots}

        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f"{self.base_url}/meet/{hash}/slots", json=payload
            ) as resp:
                resp.raise_for_status()
                return await resp.json()


termeet_client = TermeetClient()
