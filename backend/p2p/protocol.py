import orjson

class Protocol:
    @staticmethod
    def encode(message: dict) -> bytes:
        return orjson.dumps(message) + b"\n"

    @staticmethod
    def decode(stream: bytes) -> dict:
        return orjson.loads(stream)