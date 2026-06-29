import aiohttp
from grpc import aio
import grpc
from google.protobuf.empty_pb2 import Empty

from bot.src.feedback.schemas import Feedback
from bot.src.grpc.generated.service_pb2_grpc import FeedbackGRPCStub
from bot.src.grpc.generated.service_pb2 import (
    FeedbackResponseGRPC,
)

from bot.src.config import config


class TermeetClient:
    def __init__(self):
        self.base_url = config.telegram.BACKEND_API_URL.rstrip("/")
        self._grpc_channel = None

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
