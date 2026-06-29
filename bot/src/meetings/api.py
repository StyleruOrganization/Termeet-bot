import aiohttp
from grpc import aio

import grpc

from bot.src.grpc.generated.meeting_create_pb2_grpc import MeetingCreateGRPCStub
from bot.src.grpc.generated.meeting_create_pb2 import (
    MeetingCreateRequestGRPC, MeetingCreateResponseGRPC, DataRangeGRPC
)

from bot.src.config import config
from bot.src.meetings.schemas import MeetCreateResponse


class TermeetClient:
    def __init__(self):
        self.base_url = config.telegram.BACKEND_API_URL.rstrip("/")
        self._grpc_channel = None

    async def create_meeting_json(
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

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/meet/create", json=payload
            ) as response:
                response.raise_for_status()
                response: dict = await response.json()

        response: MeetCreateResponse = MeetCreateResponse(
            hash=str(response["hash"])
        )

        return response

    async def create_meeting_grpc(
        self,
        name: str,
        data_range: list,
        description: str | None = None,
        duration: str | None = None,
        link: str | None = None,
    ) -> dict:

        try:
            if self._grpc_channel is None:
                self._grpc_channel = aio.insecure_channel(
                    "host.docker.internal:50051"
                )

            stub = MeetingCreateGRPCStub(self._grpc_channel)
            message: MeetingCreateRequestGRPC = MeetingCreateRequestGRPC(
                name=name,
                data_range=[DataRangeGRPC(time_interval=slot) for slot in data_range],
                description=description,
                duration=duration,
                link=link,
            )
            response: MeetingCreateResponseGRPC = await stub.create_meeting(
                message, timeout=5
            )

        except aio.AioRpcError as e:

            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[gRPC] Сервер недоступен", flush=True)
            elif e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                print("[gRPC] Таймаут", flush=True)
            elif e.code() == grpc.StatusCode.NOT_FOUND:
                print("[gRPC] Ресурс не найден", flush=True)
            raise

        response: MeetCreateResponse = MeetCreateResponse(
            hash=str(response.hash)
        )

        return response

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
