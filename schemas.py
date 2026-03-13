from pydantic import BaseModel, HttpUrl, EmailStr, Field
from datetime import datetime
from typing import Optional, List

# Schemas para Advertiser
class AdvertiserBase(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None

class AdvertiserCreate(AdvertiserBase):
    pass

class Advertiser(AdvertiserBase):
    id: int
    balance: float
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

# Schemas para Campaign
class CampaignBase(BaseModel):
    name: str
    video_url: HttpUrl
    destination_url: HttpUrl
    budget_daily: float = Field(10.0, gt=0)
    budget_total: float = Field(100.0, gt=0)
    target_country: str = 'global'
    max_views: int = Field(1000, gt=0)

class CampaignCreate(CampaignBase):
    advertiser_id: int

class Campaign(CampaignBase):
    id: int
    advertiser_id: int
    spent: float
    views_current: int
    clicks_current: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# Schemas para Tracking
class ImpressionCreate(BaseModel):
    campaign_id: int
    viewer_ip: str
    viewer_country: Optional[str] = None

class ClickCreate(BaseModel):
    campaign_id: int
    viewer_ip: str
    impression_id: Optional[int] = None
