from pydantic import BaseModel, HttpUrl, Field, ConfigDict
from typing import List, Optional, Dict # Ensure Dict is imported
from datetime import datetime

class NewsSourceInfo(BaseModel):
    name: str
    lang: str
    img: HttpUrl

class NewsArticle(BaseModel):
    id: str
    guid: HttpUrl # Typically the URL to the article
    published_on: datetime
    imageurl: Optional[HttpUrl] = None
    title: str
    url: HttpUrl # Same as guid usually
    source: str # Source website domain / name
    body: Optional[str] = None # Or summary/description
    tags: Optional[str] = None
    categories: Optional[str] = None
    upvotes: Optional[str] = None # Or int if parsable
    downvotes: Optional[str] = None # Or int if parsable
    lang: str
    source_info: NewsSourceInfo

    model_config = ConfigDict(from_attributes=True)


class NewsApiResponse(BaseModel):
    # Based on CryptoCompare structure, may need adjustment
    # Type: Optional[str] = None
    # Message: Optional[str] = None
    # Promoted: Optional[List[Any]] = Field(default_factory=list)
    Data: List[NewsArticle] = Field(default_factory=list)
    # HasWarning: Optional[bool] = None
    # RateLimit: Optional[Dict] = None
