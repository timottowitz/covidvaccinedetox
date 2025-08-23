from fastapi import FastAPI, APIRouter, HTTPException, Query, UploadFile, File, Form
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Tuple
import uuid
from datetime import datetime, date, time, timezone
import json
import re
import math
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

# AI (local) models
class AISummaryRequest(BaseModel):
    text: Optional[str] = None
    max_sentences: int = 5

class AISummaryResponse(BaseModel):
    summary: str
    key_points: List[str]

class AIAnswerRequest(BaseModel):
    question: str
    scope: Optional[List[str]] = None

class AIAnswerReference(BaseModel):
    title: str
    link: Optional[str] = None
    type: str

class AIAnswerResponse(BaseModel):
    answer: str
    references: List[AIAnswerReference] = []

# -------------------------------------------------
# Seed Data (same as before)
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
            {"name": "NAC + Magnesium Protocol","mechanisms": ["Supports glutathione synthesis","Reduces oxidative stress","Potentially mitigates spike-induced ROS"],"dosage": "NAC 600mg twice daily; Magnesium glycinate 200-400mg daily","duration": "4-8 weeks, reassess","links": ["https://pubmed.ncbi.nlm.nih.gov/32707342/"],"tags": ["NAC", "magnesium", "antioxidant"]},
            {"name": "Spike Clearing Bundle","mechanisms": ["Reduce viral protein load","Support mitochondrial function","Improve detox pathways"],"dosage": "Follow bundle guidebook","duration": "30 days","links": ["https://www.medrxiv.org/"],"tags": ["bundle", "mitochondria", "detox"],"bundle_product": "Spike Clearance Bundle"}
        ]
        sample_treatments = [prepare_for_mongo(Treatment(**t).model_dump()) for t in sample_treatments]
        await db.treatments.insert_many(sample_treatments)

    media_count = await db.media.count_documents({})
    if media_count == 0:
        sample_media = [
            MediaItem(title='Spike Protein Lecture Clip',description='Overview of spike-induced pathways (demo).',source='YouTube',url='https://www.youtube.com/embed/dQw4w4WgXcQ',tags=['spike','lecture']).model_dump(),
            MediaItem(title='Mitochondria & Energy',description='Mitochondrial function overview (demo).',source='Vimeo',url='https://player.vimeo.com/video/76979871',tags=['mitochondria','energy']).model_dump(),
        ]
        sample_media = [prepare_for_mongo(it) for it in sample_media]
        await db.media.insert_many(sample_media)

# -------------------------------------------------
# File-based Resources Loader (auto-render)
# -------------------------------------------------
PUBLIC_RESOURCES_DIR = ROOT_DIR.parent / 'frontend' / 'public' / 'resources' / 'bioweapons'
SAMPLE_RESEARCH_JSON = ROOT_DIR.parent / 'frontend' / 'public' / 'data' / 'research-feed.json'
PUBLIC_RESOURCES_DIR.mkdir(parents=True, exist_ok=True)


def infer_kind_from_ext(ext: str) -> str:
    e = (ext or '').lower().strip('.')
    if e in ['pdf']: return 'pdf'
    if e in ['mp4', 'webm']: return 'video'
    if e in ['m4a', 'mp3', 'wav']: return 'audio'
    return 'json'


def load_metadata_file() -> Dict:
    meta_file = PUBLIC_RESOURCES_DIR / 'metadata.json'
    if meta_file.exists():
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"resources": []}
    return {"resources": []}


def save_metadata_file(meta: Dict):
    meta_file = PUBLIC_RESOURCES_DIR / 'metadata.json'
    try:
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2)
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to write metadata.json: {e}")


def load_resources_from_folder_and_meta() -> List[ResourceItem]:
    meta = load_metadata_file()
    meta_items: List[ResourceItem] = []
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
        meta_items.append(ResourceItem(
            title=m.get('title') or filename or 'Untitled',
            filename=filename,
            ext=ext,
            url=url or '',
            kind=kind,
            tags=m.get('tags', []),
            description=m.get('description'),
            uploaded_at=uploaded_dt
        ))

    seen = set([(it.filename or it.url) for it in meta_items])
    dir_items: List[ResourceItem] = []
    for p in sorted(PUBLIC_RESOURCES_DIR.glob('*')):
        if p.name == 'metadata.json' or p.is_dir():
            continue
        if p.name in seen:
            continue
        ext = p.suffix.lstrip('.')
        kind = infer_kind_from_ext(ext)
        url = f"/resources/bioweapons/{p.name}"
        stat = p.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        dir_items.append(ResourceItem(
            title=p.name,
            filename=p.name,
            ext=ext,
            url=url,
            kind=kind,
            tags=[],
            description=None,
            uploaded_at=mtime
        ))
    return meta_items + dir_items

# -------------------------------------------------
# Research Sync (omitted, unchanged)
# -------------------------------------------------
DEFAULT_FEEDS = [
    "https://pubmed.ncbi.nlm.nih.gov/rss/search/1G1RkJ2-example-spike-mitochondria/",
    "https://connect.medrxiv.org/relate/feed/181?custom=1&query=spike%20protein",
    "https://www.biorxiv.org/rss/subject/neuroscience.xml"
]

# (normalize_entry, fetch_and_sync_feeds, fallback_sync_from_sample) - same as before

# -------------------------------------------------
# Local AI helpers (same as before)
# -------------------------------------------------
STOPWORDS = set("""
a about above after again against all am an and any are as at be because been before being below between both but by could did do does doing down during each few for from further had has have having he her here hers herself him himself his how i if in into is it its itself let me more most my myself nor of on once only or other ought our ours ourselves out over own same she should so some such than that the their theirs them themselves then there these they this those through to too under until up very was we were what when where which while who whom why with would you your yours yourself yourselves
""".split())
SENT_SPLIT_RE = re.compile(r"(?<=[\.!?])\s+")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z\-']+")

# (tokenize, sentence_split, score_sentences, summarize_text, extract_keywords) - same as before

# -------------------------------------------------
# Resource management endpoints (NEW)
# -------------------------------------------------
@api.post("/resources/upload", response_model=ResourceItem)
async def upload_resource(
    file: UploadFile = File(...),
    title: Optional[str] = Form(default=None),
    tags: Optional[str] = Form(default=None),
    description: Optional[str] = Form(default=None)
):
    try:
        fname = Path(file.filename).name
        dest = PUBLIC_RESOURCES_DIR / fname
        content = await file.read()
        with open(dest, 'wb') as f:
            f.write(content)
        ext = dest.suffix.lstrip('.')
        kind = infer_kind_from_ext(ext)
        url = f"/resources/bioweapons/{fname}"
        meta = load_metadata_file()
        resources = meta.get('resources', [])
        now_iso = datetime.now(timezone.utc).isoformat()
        updated = False
        for r in resources:
            if r.get('filename') == fname or r.get('url') == url:
                if title: r['title'] = title
                if description is not None: r['description'] = description
                if tags is not None:
                    r['tags'] = [t.strip() for t in tags.split(',') if t.strip()]
                r['ext'] = ext
                r['kind'] = kind
                r['uploaded_at'] = now_iso
                updated = True
                break
        if not updated:
            resources.append({
                'title': title or fname,
                'filename': fname,
                'ext': ext,
                'url': url,
                'kind': kind,
                'tags': [t.strip() for t in (tags or '').split(',') if t.strip()],
                'description': description,
                'uploaded_at': now_iso
            })
        meta['resources'] = resources
        save_metadata_file(meta)
        item = ResourceItem(
            title=title or fname,
            filename=fname,
            ext=ext,
            url=url,
            kind=kind,
            tags=[t.strip() for t in (tags or '').split(',') if t.strip()],
            description=description,
            uploaded_at=datetime.fromisoformat(now_iso)
        )
        return item
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

class ResourceMetaUpdate(BaseModel):
    filename: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None

@api.patch("/resources/metadata", response_model=ResourceItem)
async def update_resource_metadata(body: ResourceMetaUpdate):
    meta = load_metadata_file()
    resources = meta.get('resources', [])
    idx = None
    for i, r in enumerate(resources):
        if (body.filename and r.get('filename') == body.filename) or (body.url and r.get('url') == body.url):
            idx = i
            break
    if idx is None:
        # create new metadata entry if at least url or filename provided
        if not body.filename and not body.url:
            raise HTTPException(status_code=400, detail="filename or url required")
        entry = {
            'title': body.title or (body.filename or body.url or 'Untitled'),
            'filename': body.filename,
            'ext': (Path(body.filename).suffix.lstrip('.') if body.filename else None),
            'url': body.url or (f"/resources/bioweapons/{body.filename}" if body.filename else ''),
            'kind': infer_kind_from_ext(Path(body.filename).suffix.lstrip('.')) if body.filename else 'json',
            'tags': body.tags or [],
            'description': body.description,
            'uploaded_at': datetime.now(timezone.utc).isoformat()
        }
        resources.append(entry)
        meta['resources'] = resources
        save_metadata_file(meta)
        return ResourceItem(
            title=entry['title'], filename=entry.get('filename'), ext=entry.get('ext'), url=entry.get('url'), kind=entry.get('kind'), tags=entry.get('tags', []), description=entry.get('description'), uploaded_at=datetime.fromisoformat(entry['uploaded_at'])
        )
    # update existing
    r = resources[idx]
    if body.title is not None: r['title'] = body.title
    if body.description is not None: r['description'] = body.description
    if body.tags is not None: r['tags'] = body.tags
    # persist
    meta['resources'] = resources
    save_metadata_file(meta)
    # reflect as ResourceItem
    ext = r.get('ext') or (Path(r.get('filename') or '').suffix.lstrip('.') if r.get('filename') else None)
    kind = r.get('kind') or infer_kind_from_ext(ext or '')
    uploaded_at = r.get('uploaded_at') or datetime.now(timezone.utc).isoformat()
    return ResourceItem(
        title=r.get('title') or r.get('filename') or 'Untitled',
        filename=r.get('filename'),
        ext=ext,
        url=r.get('url') or '',
        kind=kind,
        tags=r.get('tags', []),
        description=r.get('description'),
        uploaded_at=datetime.fromisoformat(uploaded_at)
    )

@api.delete("/resources/delete")
async def delete_resource(filename: Optional[str] = Query(default=None), url: Optional[str] = Query(default=None)):
    if not filename and not url:
        raise HTTPException(status_code=400, detail="filename or url required")
    meta = load_metadata_file()
    resources = meta.get('resources', [])
    # remove metadata
    new_res = []
    removed = False
    for r in resources:
        if (filename and r.get('filename') == filename) or (url and r.get('url') == url):
            removed = True
            continue
        new_res.append(r)
    meta['resources'] = new_res
    save_metadata_file(meta)
    # delete file if present
    if filename:
        try:
            p = PUBLIC_RESOURCES_DIR / Path(filename).name
            if p.exists():
                p.unlink()
        except Exception:
            pass
    return {"ok": True, "removed": removed}

# -------------------------------------------------
# Existing routes for health, feed, research, resources (GET), treatments, media, ai endpoints remain
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
    result = fetch_and_sync_feeds(DEFAULT_FEEDS)
    if result.get('parsed', 0) == 0:
        result = fallback_sync_from_sample()
    return result

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
    data = load_resources_from_folder_and_meta()
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

# AI endpoints (summarize_local, answer_local) remain defined earlier in file

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