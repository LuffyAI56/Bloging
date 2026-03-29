# Pydantic Schema Definition
# This file defines the structure of data expected in API
# requests and responses using Pydantic models.
# Import BaseModel from Pydantic
# BaseModel is the parent class used to define data schemas.
# Pydantic automatically performs:
# data validation
# type checking
# data parsing

from typing import List, Optional
from pydantic import BaseModel,Field

class Blog(BaseModel):
    title: str
    content: str

class create_user(BaseModel):
    name:str
    email:str
    password:str

class show_user(BaseModel):
    name:str
    email:str
    blogs:List[Blog]=Field(default_factory=list)
    
    class Config():
        from_attributes = True

class show_blog(BaseModel):
    title : str
    content: str
    creator : show_user
    class Config():
        from_attributes = True

class Login(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None