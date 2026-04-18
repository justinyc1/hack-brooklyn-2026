from typing import Any, Annotated
from bson import ObjectId
from pydantic import BaseModel, Field, GetCoreSchemaHandler
from pydantic_core import core_schema


class PyObjectId(str):
    """Coerces BSON ObjectId to str for Pydantic v2."""

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler):
        return core_schema.no_info_plain_validator_function(cls._validate)

    @classmethod
    def _validate(cls, v: Any) -> str:
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str) and ObjectId.is_valid(v):
            return v
        raise ValueError(f"Invalid ObjectId: {v!r}")


class MongoBase(BaseModel):
    """Base for all MongoDB documents. Maps _id → id as a string."""

    id: PyObjectId | None = Field(default=None, alias="_id")

    model_config = {"populate_by_name": True}

    @classmethod
    def from_mongo(cls, doc: dict | None):
        if doc is None:
            return None
        return cls.model_validate(doc)

    def to_mongo(self) -> dict:
        data = self.model_dump(by_alias=True, exclude_none=True)
        if "id" in data and data["id"] is not None:
            data["_id"] = ObjectId(data.pop("id"))
        elif "_id" in data and data["_id"] is not None:
            data["_id"] = ObjectId(data["_id"])
        return data
