import aiohttp
from grpc import aio
from google.protobuf.empty_pb2 import Empty

from bot.grpc.grpc_generated.service_pb2_grpc import FeedbackStub
from bot.grpc.grpc_generated.service_pb2 import FeedbackResponse

from bot.config import config
# Тест-коммент

class TermeetClient:
    def __init__(self):
        self.base_url = config.telegram.BACKEND_API_URL.rstrip("/")
        self._grpc_channel = None

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

    async def get_all_feedback_json(self) -> list:

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/feedback/get-all"
            ) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def get_all_feedback_grpc(self):
        if self._grpc_channel is None:
            self._grpc_channel = aio.insecure_channel('host.docker.internal:50051')

        stub = FeedbackStub(self._grpc_channel)
        response: FeedbackResponse = await stub.GetAllFeedback(Empty())

        return response


termeet_client = TermeetClient()
