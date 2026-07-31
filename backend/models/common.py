# backend/models/common.py
# Purpose: Shared helper so Pydantic (which validates our data) understands
# MongoDB's special ObjectId type, which it doesn't recognize by default.

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema
from bson import ObjectId

# In C++ terms, this is like writing a custom serializer/deserializer for a
# third-party type (ObjectId) so it plays nicely with a validation library
# (Pydantic) that doesn't natively know about it.
class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler: GetCoreSchemaHandler):
        # Tells Pydantic: "treat this as a string for validation purposes,
        # but underneath, values will actually be MongoDB ObjectIds."
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, value):
        if not ObjectId.is_valid(value):
            raise ValueError(f"Invalid ObjectId: {value}")
        return str(value)