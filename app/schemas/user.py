from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Annotated
from datetime import datetime
from uuid import UUID

class UserCreate(BaseModel):
    name: Annotated[str, Field(..., min_length=2, examples=["Sudhanshu Kumar"])]
    email: Annotated[EmailStr, Field(..., examples=["abc@gmail.com"])]
    password: Annotated[str, Field(..., min_length=8, examples=["abc@123456"])]

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: EmailStr
    plan: str
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"