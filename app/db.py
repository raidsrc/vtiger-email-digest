from pymongo.collection import Collection
from app.class_types import ProjectWrapperMongo
from typing import Dict

db_collections: Dict[str, Collection[ProjectWrapperMongo]] = {}
