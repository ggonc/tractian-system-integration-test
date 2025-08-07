import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

class DbHandler:
    def __init__(self):
        self._uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self._database_name = os.getenv("MONGO_DATABASE", "tractian")
        self._client: AsyncIOMotorClient | None = None
        self.db: AsyncIOMotorDatabase | None = None

    async def connect(self) -> AsyncIOMotorDatabase:
        if self._client is None:
            
            # TODO: RETRY LOGIC

            self._client = AsyncIOMotorClient(self._uri)
            self.db = self._client[self._database_name]
        return self.db

    async def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
            self.db = None
