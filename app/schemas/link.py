from pydantic import BaseModel,Field,ConfigDict,AnyHttpUrl
from typing import Annotated,Optional
from uuid import UUID,uuid4
from datetime import datetime


# id, slug, original_url, is_active, click_count, created_at

class LinkCreate(BaseModel):
    original_url: Annotated[AnyHttpUrl, Field(..., description="Original URL to shorten")]
    custom_slug:Annotated[Optional[str],Field(None,description="custom slug you want to add")]
    expires_at:Annotated[Optional[datetime],Field(None,description="Expiry time")]

class LinkResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id : UUID
    slug : str
    original_url : str
    is_active:bool
    click_count:int
    created_at:datetime