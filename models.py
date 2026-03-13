from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text
from sqlalchemy.sql import func
from database import Base

class Advertiser(Base):
    __tablename__ = 'advertisers'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    company = Column(String, nullable=True)
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

class Campaign(Base):
    __tablename__ = 'campaigns'

    id = Column(Integer, primary_key=True, index=True)
    advertiser_id = Column(Integer, index=True)
    name = Column(String, index=True)
    video_url = Column(String)
    destination_url = Column(String)
    budget_daily = Column(Float, default=10.0)
    budget_total = Column(Float, default=100.0)
    spent = Column(Float, default=0.0)
    target_country = Column(String, default='global')
    max_views = Column(Integer, default=1000)
    views_current = Column(Integer, default=0)
    clicks_current = Column(Integer, default=0)
    status = Column(String, default='active')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AdImpression(Base):
    __tablename__ = 'impressions'

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, index=True)
    viewer_ip = Column(String)
    viewer_country = Column(String, nullable=True)
    viewed_at = Column(DateTime(timezone=True), server_default=func.now())
    cost = Column(Float, default=0.01)

class AdClick(Base):
    __tablename__ = 'clicks'

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, index=True)
    impression_id = Column(Integer, nullable=True)
    viewer_ip = Column(String)
    clicked_at = Column(DateTime(timezone=True), server_default=func.now())
    cost = Column(Float, default=0.05)
