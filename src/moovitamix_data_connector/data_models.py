from datetime import datetime
from typing import List

from pydantic import BaseModel


class Track(BaseModel):
    """ Data model representing a Track from the Moovitamix API """
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
    """ Data model representing a User from the Moovitamix API """
    id: int
    first_name: str
    last_name: str
    email: str
    gender: str
    favorite_genres: str
    created_at: datetime
    updated_at: datetime

class ListenHistory(BaseModel):
    """ Data model representing a listen history from the Moovitamix API """
    user_id: int
    items: List[int]
    created_at: datetime
    updated_at: datetime
