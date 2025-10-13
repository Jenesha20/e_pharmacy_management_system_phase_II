from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class FeaturedCategory(BaseModel):
    name: str
    icon: str
    category_id: str

class HomeContent(BaseModel):
    title: str
    subtitle: str
    home_img: str
    hero_title: str
    hero_subtitle: str
    featured_categories: List[FeaturedCategory]
    trust_badges: List[dict]
    created_at: datetime
    updated_at: datetime