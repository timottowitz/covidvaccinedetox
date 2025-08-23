from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, date, time, timezone
import json
import requests
import feedparser

# -------------------------------------------------
# Env & DB
# -------------------------------------------------
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# -------------------------------------------------
# Helpers for Mongo Serialization
# -------------------------------------------------

def prepare_for_mongo(data: dict) -> dict:
    if data is None:
        return {}
    d = dict(data)
    for k, v in list(d.items()):
        if isinstance(v, datetime):
            d[k] = v.astimezone(timezone.utc).isoformat()
        elif isinstance(v, date):
            d[k] = v.isoformat()
        elif isinstance(v, time):
            d[k] = v.strftime('%H:%M:%S')
    return d


def parse_from_mongo(item: dict) -> dict:
    if not item:
        return {}
    d = dict(item)
    d.pop('_id', None)
    for k, v in list(d.items()):
        if isinstance(v, str):
            if 'T' in v and ':' in v:
                try:
                    d[k] = datetime.fromisoformat(v)
                except Exception:
                    pass
    return d

# -------------------------------------------------
# App & Router
# -------------------------------------------------
app = FastAPI()
api = APIRouter(prefix="/api")

# -------------------------------------------------
# Models
# -------------------------------------------------
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class FeedItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    title: str
    summary: str
    url: str
    tags: List[str] = []
    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: Optional[str] = None

class ResearchArticle(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    authors: List[str] = []
    published_date: date
    doi: Optional[str] = None
    link: Optional[str] = None
    abstract: Optional[str] = None
    keywords: List[str] = []
    tags: List[str] = []
    citation_count: int = 0

class ResourceItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    filename: Optional[str] = None
    ext: Optional[str] = None
    url: str
    kind: str
    tags: List[str] = []
    description: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Treatment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    mechanisms: List[str] = []
    dosage: Optional[str] = None
    duration: Optional[str] = None
    links: List[str] = []
    tags: List[str] = []
    bundle_product: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MediaItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    source: str
    url: str
    tags: List[str] = []
    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# -------------------------------------------------
# Seed Data (for MVP demo)
# -------------------------------------------------
async def ensure_seed():
    feed_count = await db.feed.count_documents({})
    if feed_count == 0:
        sample_feed = [
            FeedItem(type='article', title='Spike Protein and Mitochondrial Stress', summary='Overview of mitotoxic pathways linked to spike exposure.', url='https://doi.org/10.1101/2024.01.01.000001', tags=['spike protein','mitochondria','mechanisms'], source='bioRxiv').model_dump(),
            FeedItem(type='video', title='Microglial Activation Deep Dive', summary='Neuroinflammation pathways explained.', url='https://youtu.be/dQw4w9WgXcQ', tags=['neuroinflammation','microglia'], source='YouTube').model_dump(),
            FeedItem(type='resource', title='Bifidobacterium Decline Dataset', summary='Microbiome shifts post mRNA vaccination.', url='/resources/bioweapons/bifidobacterium-decrease.mp4', tags=['gut','bifidobacterium','dysbiosis']).model_dump(),
        ]
        sample_feed = [prepare_for_mongo(it) for it in sample_feed]
        await db.feed.insert_many(sample_feed)

    articles_count = await db.articles.count_documents({})
    if articles_count == 0:
        sample_articles = [
            ResearchArticle(
                title='Spike Protein Toxicity: A Systems Review',
                authors=['Doe J','Smith A'],
                published_date=date(2024,7,15),
                doi='10.1234/sys.2024.0715',
                link='https://pubmed.ncbi.nlm.nih.gov/000000/',
                abstract='Summarizes mechanisms including endothelial dysfunction and mitochondrial impact.',
                keywords=['spike protein','endothelium','mitochondria'],
                tags=['#spike','#mitochondria','#vascular'],
                citation_count=42
            ).model_dump(),
            ResearchArticle(
                title='IgG4 Elevation after Repeated Exposure',
                authors=['Lee K','Patel R'],
                published_date=date(2024,5,1),
                doi='10.5555/igg4.2024.0501',
                link='https://www.medrxiv.org/content/early/2024/05/01/',
                abstract='Explores immune class-switching toward IgG4 and tolerance patterns.',
                keywords=['IgG4','immune tolerance'],
                tags=['#IgG4','#immune'],
                citation_count=15
            ).model_dump(),
        ]
        sample_articles = [prepare_for_mongo(it) for it in sample_articles]
        await db.articles.insert_many(sample_articles)

    resources_count = await db.resources.count_documents({})
    if resources_count == 0:
        sample_resources = [
            ResourceItem(
                title='Spike-Protein-Toxicity.pdf',
                filename='Spike-Protein-Toxicity.pdf',
                ext='pdf',
                url='https://arxiv.org/pdf/1706.03762.pdf',
                kind='pdf',
                tags=['spike protein','mechanisms'],
                description='Reference PDF preview for demo.'
            ).model_dump(),
            ResourceItem(
                title='Bifidobacterium-Decline-clip.mp4',
                filename='bifidobacterium-decrease.mp4',
                ext='mp4',
                url='https://samplelib.com/lib/preview/mp4/sample-5s.mp4',
                kind='video',
                tags=['gut','bifidobacterium','dysbiosis'],
                description='Short sample video clip for demo.'
            ).model_dump(),
            ResourceItem(
                title='Lecture-excerpt.m4a',
                filename='lecture-excerpt.m4a',
                ext='m4a',
                url='https://samplelib.com/lib/preview/mp3/sample-3s.mp3',
                kind='audio',
                tags=['podcast','lecture'],
                description='Short sample audio for demo.'
            ).model_dump(),
        ]
        sample_resources = [prepare_for_mongo(it) for it in sample_resources]
        await db.resources.insert_many(sample_resources)

    treatments_count = await db.treatments.count_documents({})
    if treatments_count == 0:
        sample_treatments = [
            {
                "name": "NAC + Magnesium Protocol",
                "mechanisms": [
                    "Supports glutathione synthesis",
                    "Reduces oxidative stress",
                    "Potentially mitigates spike-induced ROS"
                ],
                "dosage": "NAC 600mg twice daily; Magnesium glycinate 200-400mg daily",
                "duration": "4-8 weeks, reassess",
                "links": ["https://pubmed.ncbi.nlm.nih.gov/32707342/"],
                "tags": ["NAC", "magnesium", "antioxidant"]
            },
            {
                "name": "Spike Clearing Bundle",
                "mechanisms": [
                    "Reduce viral protein load",
                    "Support mitochondrial function",
                    "Improve detox pathways"
                ],
                "dosage": "Follow bundle guidebook",
                "duration": "30 days",
                "links": ["https://www.medrxiv.org/"],
                "tags": ["bundle", "mitochondria", "detox"],
                "bundle_product": "Spike Clearance Bundle"
            }
        ]
        sample_treatments = [prepare_for_mongo(Treatment(**t).model_dump()) for t in sample_treatments]
        await db.treatments.insert_many(sample_treatments)

    media_count = await db.media.count_documents({})
    if media_count == 0:
        sample_media = [
            MediaItem(
                title='Spike Protein Lecture Clip',
                description='Overview of spike-induced pathways (demo).',
                source='YouTube',
                url='https://www.youtube.com/embed/dQw4w9WgXcQ',
                tags=['spike','lecture']
            ).model_dump(),
            MediaItem(
                title='Mitochondria & Energy',
                description='Mitochondrial function overview (demo).',
                source='Vimeo',
                url='https://player.vimeo.com/video/76979871',
                tags=['mitochondria','energy']
            ).model_dump(),
        ]
        sample_media = [prepare_for_mongo(it) for it in sample_media]
        await db.media.insert_many(sample_media)

# -------------------------------------------------
# File-based Resources Loader (auto-render)
# -------------------------------------------------
PUBLIC_RESOURCES_DIR = ROOT_DIR.parent / 'frontend' / 'public' / 'resources' / 'bioweapons'
SAMPLE_RESEARCH_JSON = ROOT_DIR.parent / 'frontend' / 'public' / 'data' / 'research-feed.json'


def infer_kind_from_ext(ext: str) -> str:
    e = (ext or '').lower().strip('.')
    if e in ['pdf']: return 'pdf'
    if e in ['mp4', 'webm']: return 'video'
    if e in ['m4a', 'mp3', 'wav']: return 'audio'
    return 'json'


def load_resources_from_folder() -> List[ResourceItem]:
    items: List[ResourceItem] = []
    meta_file = PUBLIC_RESOURCES_DIR / 'metadata.json'
    if meta_file.exists():
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            for m in meta.get('resources', []):
                url = m.get('url')
                filename = m.get('filename') or (url.split('/')[-1] if url else None)
                ext = m.get('ext') or (filename.split('.')[-1] if filename and '.' in filename else None)
                kind = m.get('kind') or infer_kind_from_ext(ext or '')
                uploaded_at = m.get('uploaded_at')
                try:
                    uploaded_dt = datetime.fromisoformat(uploaded_at) if uploaded_at else datetime.now(timezone.utc)
                except Exception:
                    uploaded_dt = datetime.now(timezone.utc)
                item = ResourceItem(
                    title=m.get('title') or filename or 'Untitled',
                    filename=filename,
                    ext=ext,
                    url=url or '',
                    kind=kind,
                    tags=m.get('tags', []),
                    description=m.get('description'),
                    uploaded_at=uploaded_dt
                )
                items.append(item)
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to parse metadata.json: {e}")
    return items

# -------------------------------------------------
# Research Sync from RSS (with fallback)
# -------------------------------------------------
DEFAULT_FEEDS = [
    # PubMed example RSS for keywords (demo URL)
    "https://pubmed.ncbi.nlm.nih.gov/rss/search/1G1RkJ2-example-spike-mitochondria/",
    # medRxiv/bioRxiv demo endpoints (not guaranteed in test env)
    "https://connect.medrxiv.org/relate/feed/181?custom=1&query=spike%20protein",
    "https://www.biorxiv.org/rss/subject/neuroscience.xml"
]


def normalize_entry(entry) -> Optional[ResearchArticle]:
    title = getattr(entry, 'title', None) or entry.get('title') if isinstance(entry, dict) else None
    link = getattr(entry, 'link', None) or entry.get('link') if isinstance(entry, dict) else None
    summary = getattr(entry, 'summary', None) or entry.get('summary') if isinstance(entry, dict) else None
    published_parsed = getattr(entry, 'published_parsed', None) or entry.get('published_parsed') if isinstance(entry, dict) else None
    published = date.today()
    if published_parsed:
        try:
            published = datetime(*published_parsed[:6], tzinfo=timezone.utc).date()
        except Exception:
            published = date.today()
    authors = []
    if hasattr(entry, 'authors'):
        authors = [a.get('name') for a in entry.authors if isinstance(a, dict) and a.get('name')]
    doi = None
    if hasattr(entry, 'links'):
        for l in entry.links:
            href = l.get('href')
            if href and 'doi.org' in href:
                doi = href.split('doi.org/')[-1]
                break
    # basic tag inference
    text = f"{title} {summary}".lower() if (title or summary) else ''
    tags = []
    if 'spike' in text: tags.append('#spike')
    if 'mitochond' in text: tags.append('#mitochondria')
    if 'gut' in text: tags.append('#gut')
    return ResearchArticle(
        title=title or 'Untitled',
        authors=authors,
        published_date=published,
        doi=doi,
        link=link,
        abstract=summary,
        keywords=[],
        tags=tags,
        citation_count=0
    )


def fetch_and_sync_feeds(feeds: List[str]) -> dict:
    added = 0
    updated = 0
    total = 0
    for url in feeds:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            parsed = feedparser.parse(resp.text)
            for entry in parsed.entries[:50]:
                art = normalize_entry(entry)
                if not art: continue
                total += 1
                # dedupe by doi or link
                q = {}
                if art.doi:
                    q['doi'] = art.doi
                elif art.link:
                    q['link'] = art.link
                else:
                    q['title'] = art.title
                existing = db.articles.find_one(q)
                if existing:
                    updated += 1
                    db.articles.update_one(q, {"$set": prepare_for_mongo(art.model_dump())})
                else:
                    db.articles.insert_one(prepare_for_mongo(art.model_dump()))
                    added += 1
        except Exception as e:
            logging.getLogger(__name__).warning(f"Feed fetch failed for {url}: {e}")
    return {"added": added, "updated": updated, "parsed": total}


def fallback_sync_from_sample() -> dict:
    if not SAMPLE_RESEARCH_JSON.exists():
        return {"added": 0, "updated": 0, "parsed": 0}
    try:
        with open(SAMPLE_RESEARCH_JSON, 'r', encoding='utf-8') as f:
            payload = json.load(f)
        added = 0
        updated = 0
        total = 0
        for it in payload.get('items', [])[:50]:
            total += 1
            art = ResearchArticle(
                title=it.get('title', 'Untitled'),
                authors=it.get('authors', []),
                published_date=date.fromisoformat(it.get('published', date.today().isoformat())),
                doi=it.get('doi'),
                link=it.get('link'),
                abstract=it.get('summary'),
                keywords=it.get('keywords', []),
                tags=['#spike'] if 'spike' in (it.get('summary','')+it.get('title','')).lower() else [],
                citation_count=0
            )
            q = {k: v for k, v in [("doi", art.doi), ("link", art.link)] if v}
            if not q:
                q = {"title": art.title}
            existing = db.articles.find_one(q)
            if existing:
                updated += 1
                db.articles.update_one(q, {"$set": prepare_for_mongo(art.model_dump())})
            else:
                db.articles.insert_one(prepare_for_mongo(art.model_dump()))
                added += 1
        return {"added": added, "updated": updated, "parsed": total}
    except Exception as e:
        logging.getLogger(__name__).warning(f"Sample feed parse failed: {e}")
        return {"added": 0, "updated": 0, "parsed": 0}

# -------------------------------------------------
# Routes
# -------------------------------------------------
@api.get("/")
async def root():
    return {"message": "mRNA Knowledge Base API"}

@api.get("/health")
async def health():
    try:
        await db.command('ping')
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.get("/research/sync")
async def research_sync():
    # Try live feeds, then fall back to local sample
    result = fetch_and_sync_feeds(DEFAULT_FEEDS)
    if result.get('parsed', 0) == 0:
        result = fallback_sync_from_sample()
    return result

@api.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_obj = StatusCheck(client_name=input.client_name)
    await db.status_checks.insert_one(prepare_for_mongo(status_obj.model_dump()))
    return status_obj

@api.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    items = await db.status_checks.find().to_list(100)
    return [StatusCheck(**parse_from_mongo(it)) for it in items]

@api.get("/feed", response_model=List[FeedItem])
async def get_feed(tag: Optional[str] = Query(default=None)):
    await ensure_seed()
    q = {"tags": {"$regex": tag, "$options": "i"}} if tag else {}
    items = await db.feed.find(q).sort("published_at", -1).to_list(100)
    return [FeedItem(**parse_from_mongo(it)) for it in items]

@api.get("/research", response_model=List[ResearchArticle])
async def get_research(tag: Optional[str] = Query(default=None), sort_by: str = Query(default='date')):
    await ensure_seed()
    q = {"tags": {"$regex": tag, "$options": "i"}} if tag else {}
    sort_field = 'published_date' if sort_by in ['date','published_date'] else ('citation_count' if sort_by == 'citations' else '_id')
    sort_dir = -1
    items = await db.articles.find(q).sort(sort_field, sort_dir).to_list(100)
    return [ResearchArticle(**parse_from_mongo(it)) for it in items]

@api.get("/resources", response_model=List[ResourceItem])
async def get_resources(tag: Optional[str] = Query(default=None)):
    folder_items = load_resources_from_folder()
    if folder_items:
        data = folder_items
    else:
        await ensure_seed()
        docs = await db.resources.find({}).sort("uploaded_at", -1).to_list(200)
        data = [ResourceItem(**parse_from_mongo(it)) for it in docs]
    if tag:
        t = tag.lower()
        data = [r for r in data if any(t in (x.lower()) for x in (r.tags or []))]
    return data

@api.get("/treatments", response_model=List[Treatment])
async def get_treatments(tag: Optional[str] = Query(default=None)):
    await ensure_seed()
    q = {"tags": {"$regex": tag, "$options": "i"}} if tag else {}
    items = await db.treatments.find(q).sort("created_at", -1).to_list(100)
    return [Treatment(**parse_from_mongo(it)) for it in items]

@api.get("/media", response_model=List[MediaItem])
async def get_media(tag: Optional[str] = Query(default=None), source: Optional[str] = Query(default=None)):
    await ensure_seed()
    q = {}
    if tag:
        q['tags'] = {"$regex": tag, "$options": "i"}
    if source:
        q['source'] = {"$regex": source, "$options": "i"}
    items = await db.media.find(q).sort("published_at", -1).to_list(100)
    return [MediaItem(**parse_from_mongo(it)) for it in items]

# bind router
app.include_router(api)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_seed():
    try:
        await ensure_seed()
    except Exception as e:
        logger.error(f"Seed error: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()