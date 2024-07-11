from datetime import datetime
from typing import List

from pydantic import BaseModel


class Track(BaseModel):
    id: int
    name: str
    artist: str
    songwriters: str
    duration: str
    genres: str
    album: str
    created_at: datetime
    updated_at: datetime

class User(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    gender: str
    favorite_genres: str
    created_at: datetime
    updated_at: datetime

class ListenHistory(BaseModel):
    user_id: int
    items: List[int]
    created_at: datetime
    updated_at: datetime
