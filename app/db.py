from pymongo import MongoClient
from pymongo.database import Database
from app.class_types import ProjectWrapperMongo


class DatabaseLayer:
    def __init__(
        self,
        uri_prefix: str = "",
        uri_address: str = "",
        username: str = "",
        password: str = "",
        db_name: str = "",
        queue_collection_name: str = "",
        trash_collection_name: str = "",
    ) -> None:
        self.uri_prefix = uri_prefix
        self.uri_address = uri_address
        self.username = username
        self.password = password
        self.db_name = db_name
        self.queue_collection_name = queue_collection_name
        self.trash_collection_name = trash_collection_name

        self.uri = f"{uri_prefix}{username}:{password}@{uri_address}"

    def connect(self):
        self.client: MongoClient[ProjectWrapperMongo] = MongoClient(self.uri)
        self.db: Database[ProjectWrapperMongo] = self.client[self.db_name]
        db = self.db
        self.queue_collection = db[self.queue_collection_name]
        self.trash_collection = db[self.trash_collection_name]

    def close(self):
        self.client.close()
