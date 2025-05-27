import asyncio
from loguru import logger
from p2p.protocol import Protocol
from p2p.peer_registry import PeerRegistry
from p2p.router import Router

class P2PNode:
    def __init__(self, agent_id: str = "agent_001", port: int = 9009):
        self.agent_id = agent_id
        self.port = port
        self.registry = PeerRegistry()
        self.router = Router(agent_id=self.agent_id)

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        logger.info(f"🔗 Подключение от {addr}")
        self.registry.add(f"{addr[0]}:{addr[1]}")

        while True:
            try:
                data = await reader.readline()
                if not data:
                    break

                message = Protocol.decode(data)
                logger.debug(f"📨 Получено сообщение: {message}")

                response = await self.router.route(message)

                writer.write(Protocol.encode(response))
                await writer.drain()
            except Exception as e:
                logger.error(f"🔥 Ошибка обработки сообщения: {e}")
                break

        writer.close()
        await writer.wait_closed()
        logger.info(f"🔌 Закрытие соединения с {addr}")

    async def start_server(self):
        """Запуск прослушивания входящих соединений"""
        server = await asyncio.start_server(
            self.handle_connection, host="0.0.0.0", port=self.port
        )
        logger.info(f"🚀 P2P сервер запущен на порту {self.port}")
        async with server:
            await server.serve_forever()

    async def send(self, host: str, port: int, message: dict) -> dict:
        """Инициировать подключение к другому узлу и отправить сообщение"""
        try:
            reader, writer = await asyncio.open_connection(host, port)
            logger.info(f"📤 Отправка на {host}:{port}: {message}")
            writer.write(Protocol.encode(message))
            await writer.drain()

            data = await reader.readline()
            response = Protocol.decode(data)
            logger.info(f"📥 Ответ от {host}:{port}: {response}")

            writer.close()
            await writer.wait_closed()
            return response
        except Exception as e:
            logger.error(f"❌ Ошибка отправки P2P-сообщения: {e}")
            return {"error": str(e)}

    def add_peer(self, host: str, port: int):
        """Явное добавление пира"""
        self.registry.add(f"{host}:{port}")

    def get_peers(self):
        return self.registry.get_all()
