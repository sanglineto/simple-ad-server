from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, Response
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime
import random

import models
import schemas
import crud
from database import SessionLocal, engine

# Criar tabelas
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title='SimpleAdServer',
    description='Plataforma profissional de anúncios',
    version='1.0.0'
)

# Configurar templates e arquivos estáticos
templates = Jinja2Templates(directory='templates')
app.mount('/static', StaticFiles(directory='static'), name='static')

# Dependência
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Rotas Web ----------
@app.get('/', response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    # Estatísticas
    total_views = db.query(models.AdImpression).count()
    total_clicks = db.query(models.AdClick).count()
    total_spent = db.query(models.Campaign).with_entities(models.Campaign.spent).all()
    total_spent = sum([s[0] for s in total_spent]) if total_spent else 0
    active_campaigns = db.query(models.Campaign).filter(
        models.Campaign.status == 'active'
    ).count()

    # Dados para o gráfico
    daily_stats = crud.get_daily_stats(db)

    return templates.TemplateResponse('dashboard.html', {
        'request': request,
        'total_views': total_views,
        'total_clicks': total_clicks,
        'total_spent': total_spent,
        'active_campaigns': active_campaigns,
        'daily_stats': json.dumps(daily_stats)
    })

@app.get('/campaigns', response_class=HTMLResponse)
async def list_campaigns(request: Request, db: Session = Depends(get_db)):
    campaigns = crud.get_campaigns(db)
    return templates.TemplateResponse('campaigns.html', {
        'request': request,
        'campaigns': campaigns
    })

@app.get('/campaigns/new', response_class=HTMLResponse)
async def new_campaign_form(request: Request, db: Session = Depends(get_db)):
    advertisers = crud.get_advertisers(db)
    return templates.TemplateResponse('campaign_form.html', {
        'request': request,
        'advertisers': advertisers
    })

@app.post('/campaigns/new')
async def create_campaign(
    request: Request,
    name: str = Form(...),
    video_url: str = Form(...),
    destination_url: str = Form(...),
    advertiser_id: int = Form(...),
    budget_daily: float = Form(10.0),
    budget_total: float = Form(100.0),
    max_views: int = Form(1000),
    target_country: str = Form('global'),
    db: Session = Depends(get_db)
):
    campaign_data = schemas.CampaignCreate(
        name=name,
        video_url=video_url,
        destination_url=destination_url,
        advertiser_id=advertiser_id,
        budget_daily=budget_daily,
        budget_total=budget_total,
        max_views=max_views,
        target_country=target_country
    )
    crud.create_campaign(db, campaign_data)
    return RedirectResponse(url='/campaigns', status_code=303)

# ---------- API de Tracking ----------
@app.get('/api/ad/{country}')
async def get_ad(country: str = 'global', db: Session = Depends(get_db)):
    campaigns = crud.get_active_campaigns(db, country)
    if not campaigns:
        return JSONResponse(status_code=404, content={'error': 'No active campaigns'})

    campaign = random.choice(campaigns)
    return {
        'campaign_id': campaign.id,
        'video_url': campaign.video_url,
        'destination_url': campaign.destination_url,
        'tracking_pixel': f'/api/track/impression/{campaign.id}'
    }

@app.get('/api/track/impression/{campaign_id}')
async def track_impression(campaign_id: int, request: Request, db: Session = Depends(get_db)):
    impression = schemas.ImpressionCreate(
        campaign_id=campaign_id,
        viewer_ip=request.client.host
    )
    crud.create_impression(db, impression)

    # Retornar pixel 1x1
    return Response(
        content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
        media_type='image/gif'
    )

@app.get('/api/track/click/{campaign_id}')
async def track_click(campaign_id: int, request: Request, db: Session = Depends(get_db)):
    click = schemas.ClickCreate(
        campaign_id=campaign_id,
        viewer_ip=request.client.host
    )
    crud.create_click(db, click)

    campaign = crud.get_campaign(db, campaign_id)
    if campaign and campaign.destination_url:
        return RedirectResponse(url=campaign.destination_url)
    return RedirectResponse(url='/')

# ---------- API de Gerenciamento ----------
@app.post('/api/advertisers/', response_model=schemas.Advertiser)
def create_advertiser(advertiser: schemas.AdvertiserCreate, db: Session = Depends(get_db)):
    db_advertiser = crud.get_advertiser_by_email(db, advertiser.email)
    if db_advertiser:
        raise HTTPException(status_code=400, detail='Email already registered')
    return crud.create_advertiser(db, advertiser)

@app.get('/api/advertisers/', response_model=List[schemas.Advertiser])
def read_advertisers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_advertisers(db, skip, limit)

@app.post('/api/campaigns/', response_model=schemas.Campaign)
def create_campaign_api(campaign: schemas.CampaignCreate, db: Session = Depends(get_db)):
    return crud.create_campaign(db, campaign)

@app.get('/api/campaigns/', response_model=List[schemas.Campaign])
def read_campaigns(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_campaigns(db, skip, limit)

@app.get('/api/stats/')
def get_stats(days: int = 7, db: Session = Depends(get_db)):
    return crud.get_daily_stats(db, days)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000, reload=True)
