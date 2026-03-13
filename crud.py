from sqlalchemy.orm import Session
from sqlalchemy import func
import models
import schemas
from datetime import datetime, timedelta

# ---------- Advertisers ----------
def get_advertiser(db: Session, advertiser_id: int):
    return db.query(models.Advertiser).filter(models.Advertiser.id == advertiser_id).first()

def get_advertiser_by_email(db: Session, email: str):
    return db.query(models.Advertiser).filter(models.Advertiser.email == email).first()

def get_advertisers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Advertiser).offset(skip).limit(limit).all()

def create_advertiser(db: Session, advertiser: schemas.AdvertiserCreate):
    db_advertiser = models.Advertiser(**advertiser.model_dump())
    db.add(db_advertiser)
    db.commit()
    db.refresh(db_advertiser)
    return db_advertiser

# ---------- Campaigns ----------
def get_campaign(db: Session, campaign_id: int):
    return db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()

def get_active_campaigns(db: Session, country: str = 'global'):
    query = db.query(models.Campaign).filter(
        models.Campaign.status == 'active',
        models.Campaign.views_current < models.Campaign.max_views
    )
    if country != 'global':
        query = query.filter(
            (models.Campaign.target_country == 'global') |
            (models.Campaign.target_country == country)
        )
    return query.all()

def get_campaigns(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Campaign).offset(skip).limit(limit).all()

def create_campaign(db: Session, campaign: schemas.CampaignCreate):
    campaign_dict = campaign.model_dump()
    # Converter HttpUrl para string
    campaign_dict['video_url'] = str(campaign_dict['video_url'])
    campaign_dict['destination_url'] = str(campaign_dict['destination_url'])

    db_campaign = models.Campaign(**campaign_dict)
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

def update_campaign_stats(db: Session, campaign_id: int, view: bool = False, click: bool = False):
    campaign = get_campaign(db, campaign_id)
    if campaign:
        if view:
            campaign.views_current += 1
            campaign.spent += 0.01
        if click:
            campaign.clicks_current += 1
            campaign.spent += 0.05
        if campaign.views_current >= campaign.max_views or campaign.spent >= campaign.budget_total:
            campaign.status = 'completed'
        db.commit()
        db.refresh(campaign)
    return campaign

# ---------- Tracking ----------
def create_impression(db: Session, impression: schemas.ImpressionCreate):
    db_impression = models.AdImpression(**impression.model_dump())
    db.add(db_impression)
    db.commit()
    db.refresh(db_impression)
    update_campaign_stats(db, impression.campaign_id, view=True)
    return db_impression

def create_click(db: Session, click: schemas.ClickCreate):
    db_click = models.AdClick(**click.model_dump())
    db.add(db_click)
    db.commit()
    db.refresh(db_click)
    update_campaign_stats(db, click.campaign_id, click=True)
    return db_click

def get_daily_stats(db: Session, days: int = 7):
    date_limit = datetime.now() - timedelta(days=days)

    impressions = db.query(
        func.date(models.AdImpression.viewed_at).label('date'),
        func.count().label('count')
    ).filter(models.AdImpression.viewed_at >= date_limit)\
     .group_by(func.date(models.AdImpression.viewed_at)).all()

    clicks = db.query(
        func.date(models.AdClick.clicked_at).label('date'),
        func.count().label('count')
    ).filter(models.AdClick.clicked_at >= date_limit)\
     .group_by(func.date(models.AdClick.clicked_at)).all()

    return {
        'impressions': {str(d.date): d.count for d in impressions},
        'clicks': {str(d.date): d.count for d in clicks}
    }
