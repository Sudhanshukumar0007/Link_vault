from pydantic import BaseModel, Field, ConfigDict, AnyHttpUrl, field_validator
import re
from typing import Annotated,Optional
from uuid import UUID,uuid4
from datetime import datetime

class LinkCreate(BaseModel):
    original_url: Annotated[AnyHttpUrl, Field(..., description="Original URL to shorten")]
    custom_slug: Annotated[Optional[str], Field(None, min_length=3, max_length=12)]
    expires_at: Annotated[Optional[datetime], Field(None)]

    @field_validator("custom_slug")
    @classmethod
    def validate_slug(cls, v):
        if v is None:
            return v
        if not re.match(r'^[a-zA-Z0-9-_]+$', v):
            raise ValueError("Slug can only contain letters, numbers, hyphens and underscores")
        return v

class LinkResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id : UUID
    slug : str
    original_url : str
    is_active:bool
    click_count:int
    created_at:datetime