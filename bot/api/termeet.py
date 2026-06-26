import aiohttp
from grpc import aio
from google.protobuf.empty_pb2 import Empty
import grpc

from bot.grpc.grpc_generated.service_pb2_grpc import FeedbackGRPCStub
from bot.grpc.grpc_generated.service_pb2 import (
    FeedbackResponseGRPC,
)

from bot.config import config
from bot.api.schemas import Feedback


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

    async def get_all_feedback_json(self) -> list[Feedback]:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/feedback/get-all"
                ) as response:
                    response.raise_for_status()
                    response: list[dict] = await response.json()

                    response: list[Feedback] = [
                        Feedback.model_validate(f) for f in response
                    ]

                    return response

            except aiohttp.ClientResponseError as e:
                # HTTP ошибки: 404, 500 и т.д.
                print(f"[REST] HTTP ошибка: {e.status} — {e.message}")
                raise

            except aiohttp.ClientConnectionError as e:
                # Сервер недоступен, нет соединения
                print(f"[REST] Ошибка соединения: {e}")
                raise

            except aiohttp.ServerTimeoutError as e:
                # Таймаут
                print(f"[REST] Таймаут: {e}")
                raise

    async def get_all_feedback_grpc(self) -> list[Feedback]:
        try:
            if self._grpc_channel is None:
                self._grpc_channel = aio.insecure_channel(
                    "host.docker.internal:50051"
                )

            stub = FeedbackGRPCStub(self._grpc_channel)
            response: FeedbackResponseGRPC = await stub.GetAllFeedback(
                Empty(), timeout=5
            )

            response: list[Feedback] = [
                Feedback.from_grpc(f) for f in response.feedbacks
            ]

            return response

        except aio.AioRpcError as e:
            # Все gRPC ошибки
            print(f"[gRPC] Ошибка: {e.code()} — {e.details()}")

            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[gRPC] Сервер недоступен")
            elif e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                print("[gRPC] Таймаут")
            elif e.code() == grpc.StatusCode.NOT_FOUND:
                print("[gRPC] Ресурс не найден")

            raise


termeet_client = TermeetClient()
