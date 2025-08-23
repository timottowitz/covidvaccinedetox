from fastapi import FastAPI, APIRouter, HTTPException, Query, UploadFile, File, Form, BackgroundTasks, Header
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Tuple, Any, Callable
from typing_extensions import TypedDict
import uuid
from datetime import datetime, date, time, timezone
import json
import re
import math
import requests
import feedparser
import threading
import time
import asyncio
from enum import Enum
import magic
import hashlib
import yaml

# -------------------------------------------------
# Text Processing Constants and Functions
# -------------------------------------------------
WORD_RE = re.compile(r'\b\w+\b')
SENT_SPLIT_RE = r'[.!?]+\s+'
STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
    'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
    'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
    'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your',
    'his', 'its', 'our', 'their', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
    'after', 'above', 'below', 'between', 'among', 'all', 'any', 'both', 'each', 'few', 'more',
    'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
    'too', 'very', 'just', 'now'
}

def tokenize(text: str) -> List[str]:
    return [w.lower() for w in WORD_RE.findall(text or '')]


def sentence_split(text: str) -> List[str]:
    return re.split(SENT_SPLIT_RE, text.strip()) if text else []


def score_sentences(text: str) -> Tuple[List[Tuple[int, float]], Dict[str, float]]:
    sentences = sentence_split(text)
    tokens = tokenize(text)
    freqs: Dict[str, int] = {}
    for t in tokens:
        if t in STOPWORDS: continue
        freqs[t] = freqs.get(t, 0) + 1
    if not freqs:
        return [], {}
    max_f = max(freqs.values()) or 1
    weights = {w: f / max_f for w, f in freqs.items()}
    scores: List[Tuple[int, float]] = []
    for idx, s in enumerate(sentences):
        stoks = tokenize(s)
        score = sum(weights.get(t, 0.0) for t in stoks)
        score = score / (len(stoks) + 1e-6)
        scores.append((idx, score))
    return scores, weights


def summarize_text(text: str, max_sentences: int = 5) -> Tuple[str, List[str]]:
    if not text:
        return "", []
    scores, weights = score_sentences(text)
    if not scores:
        return (text.split("\n")[0][:280] + ("..." if len(text) > 280 else "")), []
    top = sorted(scores, key=lambda x: x[1], reverse=True)[:max_sentences]
    # restore original order for readability
    sents = sentence_split(text)
    top_sorted = [s for i, s in sorted([(i, sents[i]) for i, _ in top], key=lambda x: x[0])]
    summary = " ".join(top_sorted)
    top_keywords = [w for w, _ in sorted(weights.items(), key=lambda kv: kv[1], reverse=True)[:6] if len(w) > 3]
    key_points = [f"{w.capitalize()}" for w in top_keywords]
    return summary, key_points


def extract_keywords(q: str, top_k: int = 6) -> List[str]:
    tokens = [t for t in tokenize(q) if t not in STOPWORDS and len(t) > 3]
    freqs: Dict[str, int] = {}
    for t in tokens:
        freqs[t] = freqs.get(t, 0) + 1
    return [w for w, _ in sorted(freqs.items(), key=lambda kv: kv[1], reverse=True)[:top_k]]

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
    thumbnail_url: Optional[str] = None
    knowledge_url: Optional[str] = None
    knowledge_job_id: Optional[str] = None
    knowledge_job_type: Optional[str] = None
    knowledge_hash: Optional[str] = None


# -------------------------------------------------
# Task Tracking Models
# -------------------------------------------------
class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"


class TaskInfo(BaseModel):
    task_id: str
    idempotency_key: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    resource_filename: Optional[str] = None
    resource_url: Optional[str] = None
    result: Optional[ResourceItem] = None
    error_message: Optional[str] = None


class TaskResponse(BaseModel):
    task_id: str
    idempotency_key: str
    status: TaskStatus = TaskStatus.PENDING
    message: str = "Upload task created successfully"


# In-memory task storage (for MVP - could be replaced with Redis/DB later)
tasks_storage: Dict[str, TaskInfo] = {}


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
# Seed Data
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
            MediaItem(title='Spike Protein Lecture Clip',description='Overview of spike-induced pathways (demo).',source='YouTube',url='https://www.youtube.com/embed/dQw4w9WgXcQ',tags=['spike','lecture']).model_dump(),
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
THUMBS_DIR = PUBLIC_RESOURCES_DIR / 'thumbnails'
THUMBS_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------
# Knowledge base integration (Chunkr & Gemini)
# -------------------------
KNOWLEDGE_DIR = ROOT_DIR.parent / 'frontend' / 'public' / 'knowledge'
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

CHUNKR_API_KEY = os.environ.get('CHUNKR_API_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# File upload constants  
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'video/mp4', 
    'video/quicktime',
    'video/webm'
}


def validate_file_upload(file: UploadFile) -> Tuple[bool, Optional[str]]:
    """Validate file size and MIME type. Returns (is_valid, error_message)"""
    if file.size and file.size > MAX_FILE_SIZE:
        return False, f"File size {file.size} exceeds maximum allowed size of {MAX_FILE_SIZE} bytes"
    
    # Use python-magic to detect MIME type from content
    try:
        file_content = file.file.read(2048)  # Read first 2KB for MIME detection
        file.file.seek(0)  # Reset file pointer
        detected_mime = magic.from_buffer(file_content, mime=True)
        
        if detected_mime not in ALLOWED_MIME_TYPES:
            return False, f"File type '{detected_mime}' not allowed. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
            
    except Exception as e:
        logging.getLogger(__name__).warning(f"MIME type detection failed: {e}")
        # Fallback to content_type header if magic fails
        if file.content_type not in ALLOWED_MIME_TYPES:
            return False, f"File type '{file.content_type}' not allowed. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
    
    return True, None


def create_task(idempotency_key: str, resource_filename: str = None) -> TaskInfo:
    """Create a new upload task"""
    task_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    task_info = TaskInfo(
        task_id=task_id,
        idempotency_key=idempotency_key,
        status=TaskStatus.PENDING,
        created_at=now,
        updated_at=now,
        resource_filename=resource_filename
    )
    
    tasks_storage[task_id] = task_info
    return task_info


def get_task(task_id: str) -> Optional[TaskInfo]:
    """Get task by ID"""
    return tasks_storage.get(task_id)


def update_task_status(task_id: str, status: TaskStatus, result: ResourceItem = None, error_message: str = None) -> bool:
    """Update task status and result"""
    if task_id not in tasks_storage:
        return False
        
    task_info = tasks_storage[task_id]
    task_info.status = status
    task_info.updated_at = datetime.now(timezone.utc)
    
    if result:
        task_info.result = result
    if error_message:
        task_info.error_message = error_message
        
    return True


def find_task_by_idempotency_key(idempotency_key: str) -> Optional[TaskInfo]:
    """Find existing task by idempotency key"""
    for task_info in tasks_storage.values():
        if task_info.idempotency_key == idempotency_key:
            return task_info
    return None


def _write_markdown_atomic(path: Path, content: str) -> None:
    try:
        tmp = path.with_suffix(path.suffix + '.tmp')
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(content)
        os.replace(tmp, path)
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to write markdown {path}: {e}")


def _unique_knowledge_path(slug: str, suffix: str = "") -> Path:
    base = f"{slug}{suffix}.md"
    p = KNOWLEDGE_DIR / base
    if not p.exists():
        return p
    i = 2
    while True:
        cand = KNOWLEDGE_DIR / f"{slug}{suffix}-{i}.md"
        if not cand.exists():
            return cand
        i += 1


def _update_metadata_knowledge(resource_filename: Optional[str], resource_url: Optional[str], knowledge_url: str, knowledge_hash: Optional[str] = None) -> None:
    try:
        meta = load_metadata_file()
        resources = meta.get('resources', [])
        updated = False
        for r in resources:
            if (resource_filename and r.get('filename') == resource_filename) or (resource_url and r.get('url') == resource_url):
                r['knowledge_url'] = knowledge_url
                if knowledge_hash:
                    r['knowledge_hash'] = knowledge_hash
                updated = True
                break
        if updated:
            meta['resources'] = resources
            save_metadata_file(meta)
    except Exception as e:
        logging.getLogger(__name__).warning(f"_update_metadata_knowledge error: {e}")


def chunkr_ingest_pdf_bg(file_path_str: str, title: str, tags: List[str], description: Optional[str], resource_filename: Optional[str] = None, resource_url: Optional[str] = None) -> Optional[str]:
    if not CHUNKR_API_KEY:
        return None
    try:
        headers = {"Authorization": f"Bearer {CHUNKR_API_KEY}"}
        with open(file_path_str, 'rb') as fh:
            files = {"file": (Path(file_path_str).name, fh, 'application/pdf')}
            data = {
                "source_type": "research_article",
                "metadata": json.dumps({
                    "title": title,
                    "tags": tags,
                    "description": description or ""
                })
            }
            resp = requests.post("https://api.chunkr.ai/v1/ingest", headers=headers, data=data, files=files, timeout=120)
        if resp.status_code != 200:
            logging.getLogger(__name__).warning(f"Chunkr ingest failed: {resp.status_code} {resp.text}")
            return None
        result = resp.json()
        ingest_id = result.get('id') or str(uuid.uuid4())
        summary = result.get('summary') or ""
        key_points = result.get('key_points') or []
        chunks = result.get('chunks') or []
        meta = result.get('metadata') or {}
        source_url = result.get('source_url') or ""
        kp_md = "\n".join([f"- **{p}**" for p in key_points])
        chunks_parts: List[str] = []
        for i, c in enumerate(chunks):
            idx = c.get('chunk_index', i)
            pg = c.get('page_number', '?')
            txt = c.get('text', '') or ''
            chunks_parts.append(f"\n### Chunk {idx} (p{pg})\n\n{txt}\n")
        chunks_md = "".join(chunks_parts)
        tags_join = ", ".join(meta.get('tags') or tags)
        title_md = meta.get('title') or title
        date_str = datetime.now(timezone.utc).date().isoformat()
        sanitized_summary = summary.replace('"', '\\"')
        md_lines = [
            "---",
            f"title: {title_md}",
            f"source: {source_url}",
            "type: research_article",
            f"tags: {tags_join}",
            f"date: {date_str}",
            f"summary: \"{sanitized_summary}\"",
            "---",
            "",
            "## Key Points",
            "",
            kp_md,
            "",
            "## Full Text (Chunks)",
            "",
            chunks_md
        ]
        md = "\n".join(md_lines)
        # make nice slug from title
        slug = re.sub(r"[^a-zA-Z0-9_\-]+","-", (title_md or "document").lower()).strip('-')[:80] or "document"
        out = _unique_knowledge_path(slug)
        _write_markdown_atomic(out, md)
        url = f"/knowledge/{out.name}"
        
        # Compute content hash for the generated markdown
        content_hash = compute_content_hash(out)
        
        # persist mapping to metadata if resource info provided
        if resource_filename or resource_url:
            _update_metadata_knowledge(resource_filename, resource_url, url, content_hash)
        return url
    except Exception as e:
        logging.getLogger(__name__).warning(f"chunkr_ingest_pdf_bg error: {e}")
        return None


async def process_upload_task(task_id: str, file_content: bytes, filename: str, title: str = None, tags: str = None, description: str = None):
    """Process upload task in background"""
    try:
        # Update task status to processing
        update_task_status(task_id, TaskStatus.PROCESSING)
        
        # Save file to disk
        fname = Path(filename).name
        dest = PUBLIC_RESOURCES_DIR / fname
        
        with open(dest, 'wb') as f:
            f.write(file_content)
            
        ext = dest.suffix.lstrip('.')
        kind = infer_kind_from_ext(ext)
        url = f"/resources/bioweapons/{fname}"
        
        # Update metadata
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
        
        # Generate thumbnail synchronously
        thumb_url = None
        if kind in ('pdf','video'):
            temp_res = ResourceItem(
                title=title or fname, 
                filename=fname, 
                ext=ext, 
                url=url, 
                kind=kind, 
                tags=[t.strip() for t in (tags or '').split(',') if t.strip()], 
                description=description, 
                uploaded_at=datetime.fromisoformat(now_iso)
            )
            thumb_url = ensure_thumbnail_for_resource(temp_res, prefer_time_sec=1.0)
            
        # Trigger background knowledge ingestion
        knowledge_job_id = None
        knowledge_job_type = None
        
        try:
            if kind == 'pdf':
                knowledge_job_id = str(uuid.uuid4())
                knowledge_job_type = 'chunkr_pdf'
                # Start background task but don't wait
                asyncio.create_task(run_chunkr_ingest_pdf_bg(dest.as_posix(), title or fname, [t.strip() for t in (tags or '').split(',') if t.strip()], description, fname, url))
            elif kind == 'video':
                knowledge_job_id = str(uuid.uuid4())
                knowledge_job_type = 'gemini_video'
                # Start background task but don't wait
                asyncio.create_task(run_gemini_summarize_video_bg(dest.as_posix(), title or fname, fname, url))
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to enqueue background ingestion: {e}")
            
        # Create result
        result = ResourceItem(
            title=title or fname,
            filename=fname,
            ext=ext,
            url=url,
            kind=kind,
            tags=[t.strip() for t in (tags or '').split(',') if t.strip()],
            description=description,
            uploaded_at=datetime.fromisoformat(now_iso),
            thumbnail_url=thumb_url,
            knowledge_url=None,
            knowledge_job_id=knowledge_job_id,
            knowledge_job_type=knowledge_job_type
        )
        
        # Update task status to completed
        update_task_status(task_id, TaskStatus.COMPLETED, result=result)
        
    except Exception as e:
        error_msg = f"Upload processing failed: {str(e)}"
        logging.getLogger(__name__).error(error_msg)
        update_task_status(task_id, TaskStatus.FAILED, error_message=error_msg)


async def run_chunkr_ingest_pdf_bg(file_path_str: str, title: str, tags: List[str], description: str, resource_filename: str, resource_url: str):
    """Async wrapper for chunkr ingestion"""
    await asyncio.get_event_loop().run_in_executor(None, chunkr_ingest_pdf_bg, file_path_str, title, tags, description, resource_filename, resource_url)


async def run_gemini_summarize_video_bg(file_path_str: str, title: str, resource_filename: str, resource_url: str):
    """Async wrapper for gemini summarization"""
    await asyncio.get_event_loop().run_in_executor(None, gemini_summarize_video_bg, file_path_str, title, resource_filename, resource_url)


def gemini_summarize_video_bg(file_path_str: str, title: str, resource_filename: Optional[str] = None, resource_url: Optional[str] = None) -> Optional[str]:
    if not GEMINI_API_KEY:
        return None
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        uploaded = client.files.upload(file=file_path_str)
        import time
        for _ in range(30):
            info = client.files.get(name=uploaded.name)
            if getattr(info, 'state', None) == 'ACTIVE':
                break
            time.sleep(2)
        prompt = "Provide a structured markdown summary with sections: Main Topics, Summary, Key Points, Timestamps, Action Items."
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=[uploaded, prompt])
        text = getattr(resp, 'text', None) or ""
        if not text:
            return None
        date_str = datetime.now(timezone.utc).date().isoformat()
        md = "\n".join([
            "---",
            f"title: {title}",
            "type: video",
            f"date: {date_str}",
            "---",
            "",
            text
        ])
        slug = re.sub(r"[^a-zA-Z0-9_\-]+","-", (title or "video").lower()).strip('-')[:80] or "video"
        out = _unique_knowledge_path(slug, suffix="_video")
        _write_markdown_atomic(out, md)
        url = f"/knowledge/{out.name}"
        
        try:
            client.files.delete(name=uploaded.name)
        except Exception:
            pass
            
        # Compute content hash for the generated markdown
        content_hash = compute_content_hash(out)
        
        if resource_filename or resource_url:
            _update_metadata_knowledge(resource_filename, resource_url, url, content_hash)
        return url
    except Exception as e:
        logging.getLogger(__name__).warning(f"gemini_summarize_video_bg error: {e}")
        return None


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


# ---------- Thumbnails helpers ----------

def _safe_slug(name: str) -> str:
    base = re.sub(r'\s+', '-', (name or '').strip())
    base = re.sub(r'[^a-zA-Z0-9_\-\.]+', '-', base)
    base = base.strip('-').lower()
    return base or 'resource'


def _letterbox_image(pil_img, size=(480, 270), color=(16, 16, 16)):
    try:
        from PIL import Image
    except Exception:
        return None
    if pil_img is None:
        return None
    w, h = pil_img.size
    target_w, target_h = size
    # scale
    scale = min(target_w / max(1, w), target_h / max(1, h))
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    pil_resized = pil_img.resize((new_w, new_h))
    canvas = Image.new('RGB', size, color)
    offset = ((target_w - new_w) // 2, (target_h - new_h) // 2)
    canvas.paste(pil_resized, offset)
    return canvas


def _generate_pdf_thumbnail(src_path: Path, dst_path: Path) -> bool:
    try:
        import fitz  # PyMuPDF
        from PIL import Image
    except Exception as e:
        logging.getLogger(__name__).warning(f"PDF thumbnail deps missing: {e}")
        return False
    try:
        doc = fitz.open(src_path.as_posix())
        if doc.page_count == 0:
            return False
        page = doc.load_page(0)
        pix = page.get_pixmap(alpha=False, dpi=144)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img = _letterbox_image(img)
        if img is None:
            return False
        img.save(dst_path.as_posix(), format='JPEG', quality=85)
        return True
    except Exception as e:
        logging.getLogger(__name__).warning(f"PDF thumbnail generation failed for {src_path}: {e}")
        return False


def _generate_video_thumbnail(src_path: Path, dst_path: Path, time_sec: float = 1.0) -> bool:
    try:
        import cv2
        from PIL import Image
    except Exception as e:
        logging.getLogger(__name__).warning(f"Video thumbnail deps missing: {e}")
        return False
    try:
        cap = cv2.VideoCapture(src_path.as_posix())
        if not cap.isOpened():
            logging.getLogger(__name__).warning(f"Video open failed: {src_path}")
            return False
        fps = cap.get(cv2.CAP_PROP_FPS) or 0
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        frame_index = int(fps * time_sec) if fps > 0 else 0
        # fallback to midpoint if 1s beyond video
        if fps > 0 and frame_count > 0 and frame_index >= frame_count:
            frame_index = int(frame_count // 2)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = cap.read()
        if not ok or frame is None:
            # try first frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = cap.read()
        cap.release()
        if not ok or frame is None:
            return False
        # BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        img = _letterbox_image(img)
        if img is None:
            return False
        img.save(dst_path.as_posix(), format='JPEG', quality=85)
        return True
    except Exception as e:
        logging.getLogger(__name__).warning(f"Video thumbnail generation failed for {src_path}: {e}")
        return False


def _download_to_temp(url: str, suffix: str = '') -> Optional[Path]:
    import tempfile
    try:
        r = requests.get(url, timeout=15, stream=True)
        if r.status_code != 200:
            return None
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        os.close(tmp_fd)
        with open(tmp_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 512):
                if not chunk:
                    break
                f.write(chunk)
        return Path(tmp_path)
    except Exception:
        return None


def ensure_thumbnail_for_resource(res: 'ResourceItem', prefer_time_sec: float = 1.0) -> Optional[str]:
    try:
        kind = (res.kind or '').lower()
        ext = (res.ext or '').lower()
        if kind not in ('pdf', 'video'):
            return None
        # slug
        base_name = res.filename or (Path(res.url).name if res.url else 'resource')
        slug = Path(_safe_slug(Path(base_name).stem)).stem
        dst = THUMBS_DIR / f"{slug}.jpg"
        if dst.exists():
            return f"/resources/bioweapons/thumbnails/{dst.name}"
        # find source
        src_path: Optional[Path] = None
        # local url
        if res.url and res.url.startswith('/resources/bioweapons/'):
            candidate = PUBLIC_RESOURCES_DIR / Path(res.url).name
            if candidate.exists():
                src_path = candidate
        # local filename
        if src_path is None and res.filename:
            candidate = PUBLIC_RESOURCES_DIR / res.filename
            if candidate.exists():
                src_path = candidate
        # remote download
        temp_path: Optional[Path] = None
        if src_path is None and res.url and res.url.startswith('http'):
            temp_path = _download_to_temp(res.url, suffix=f".{ext or 'bin'}")
            if temp_path and temp_path.exists():
                src_path = temp_path
        if src_path is None:
            return None
        ok = False
        if kind == 'pdf' or ext == 'pdf':
            ok = _generate_pdf_thumbnail(src_path, dst)
        elif kind == 'video' or ext in ('mp4', 'webm'):
            ok = _generate_video_thumbnail(src_path, dst, time_sec=prefer_time_sec)
        # cleanup temp
        try:
            if temp_path and temp_path.exists():
                temp_path.unlink(missing_ok=True)
        except Exception:
            pass
        if ok and dst.exists():
            return f"/resources/bioweapons/thumbnails/{dst.name}"
        return None
    except Exception as e:
        logging.getLogger(__name__).warning(f"ensure_thumbnail_for_resource failed: {e}")
        return None


# -------------------------------------------------
# Advanced Reconciliation System
# -------------------------------------------------
class ReconcileResult(TypedDict):
    linked: List[str]
    updated: List[str] 
    skipped: List[str]
    conflicts: List[str]


def compute_content_hash(file_path: Path) -> str:
    """Compute SHA256 hash of markdown file content (excluding frontmatter)"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Split frontmatter and content
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                # Content after frontmatter
                body_content = parts[2].strip()
            else:
                body_content = content
        else:
            body_content = content
            
        return hashlib.sha256(body_content.encode('utf-8')).hexdigest()
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to compute hash for {file_path}: {e}")
        return ""


def parse_knowledge_frontmatter(file_path: Path) -> Dict[str, Any]:
    """Parse YAML frontmatter from knowledge markdown file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if not content.startswith('---'):
            return {}
            
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}
            
        frontmatter_yaml = parts[1].strip()
        if not frontmatter_yaml:
            return {}
            
        return yaml.safe_load(frontmatter_yaml) or {}
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to parse frontmatter for {file_path}: {e}")
        return {}


def fuzzy_match_resource(knowledge_file: Path, frontmatter: Dict[str, Any], resources: List[dict]) -> Optional[dict]:
    """Fuzzy match knowledge file to resource by title and date"""
    km_title = frontmatter.get('title', '').lower()
    km_date = frontmatter.get('date', '')
    
    if not km_title:
        return None
        
    # Score each resource
    best_match = None
    best_score = 0
    
    for resource in resources:
        if resource.get('knowledge_url'):  # Skip already linked
            continue
            
        score = 0
        res_title = (resource.get('title') or '').lower()
        res_date = resource.get('uploaded_at', '')
        
        # Title similarity (simple word overlap)
        if km_title and res_title:
            # Clean up resource title by removing file extensions and splitting on common separators
            res_title_clean = res_title.replace('.pdf', '').replace('.mp4', '').replace('.m4a', '').replace('.webm', '')
            km_words = set(km_title.replace('-', ' ').split())
            res_words = set(res_title_clean.replace('-', ' ').replace('_', ' ').split())
            if km_words and res_words:
                overlap = len(km_words & res_words)
                similarity = overlap / max(len(km_words), len(res_words))
                score += similarity * 0.7
        
        # Date proximity (if both have dates)
        if km_date and res_date:
            try:
                km_dt = datetime.fromisoformat(km_date.replace('Z', '+00:00')) if isinstance(km_date, str) else km_date
                res_dt = datetime.fromisoformat(res_date.replace('Z', '+00:00')) if isinstance(res_date, str) else res_date
                
                # Same day = 0.3 points, within week = 0.2, within month = 0.1
                diff_days = abs((km_dt - res_dt).days)
                if diff_days == 0:
                    score += 0.3
                elif diff_days <= 7:
                    score += 0.2
                elif diff_days <= 30:
                    score += 0.1
            except (ValueError, TypeError):
                pass
        
        if score > best_score and score > 0.5:  # Minimum threshold
            best_score = score
            best_match = resource
            
    return best_match


def advanced_knowledge_reconcile() -> ReconcileResult:
    """Advanced reconciliation with hash-based matching and detailed reporting"""
    result: ReconcileResult = {
        'linked': [],
        'updated': [],
        'skipped': [],
        'conflicts': []
    }
    
    try:
        meta = load_metadata_file()
        resources = meta.get('resources', [])
        
        if not resources:
            return result
            
        # Build lookup maps
        resource_by_id = {r.get('id'): r for r in resources if r.get('id')}
        resource_by_hash = {r.get('knowledge_hash'): r for r in resources if r.get('knowledge_hash')}
        
        for md_file in sorted(KNOWLEDGE_DIR.glob('*.md')):
            file_rel_path = f"/knowledge/{md_file.name}"
            
            # Parse frontmatter and compute hash
            frontmatter = parse_knowledge_frontmatter(md_file)
            content_hash = compute_content_hash(md_file)
            
            if not content_hash:
                result['skipped'].append(f"{md_file.name}: failed to compute hash")
                continue
                
            matched_resource = None
            match_type = None
            
            # Precedence 1: resource_id in frontmatter
            resource_id = frontmatter.get('resource_id')
            if resource_id and resource_id in resource_by_id:
                candidate = resource_by_id[resource_id]
                if not candidate.get('knowledge_url'):
                    matched_resource = candidate
                    match_type = "resource_id"
                elif candidate.get('knowledge_url') != file_rel_path:
                    result['conflicts'].append(f"{md_file.name}: resource_id {resource_id} already linked to {candidate.get('knowledge_url')}")
                    continue
                else:
                    # Already correctly linked
                    if candidate.get('knowledge_hash') != content_hash:
                        candidate['knowledge_hash'] = content_hash
                        result['updated'].append(f"{md_file.name}: updated hash for existing link")
                    else:
                        result['skipped'].append(f"{md_file.name}: already correctly linked")
                    continue
            
            # Precedence 2: stored hash match
            if not matched_resource and content_hash in resource_by_hash:
                candidate = resource_by_hash[content_hash]
                if not candidate.get('knowledge_url'):
                    matched_resource = candidate
                    match_type = "hash"
                elif candidate.get('knowledge_url') != file_rel_path:
                    result['conflicts'].append(f"{md_file.name}: hash {content_hash[:8]} already linked to {candidate.get('knowledge_url')}")
                    continue
                else:
                    # Already correctly linked by hash
                    result['skipped'].append(f"{md_file.name}: already linked by hash")
                    continue
            
            # Precedence 3: fuzzy match on title/date
            if not matched_resource:
                matched_resource = fuzzy_match_resource(md_file, frontmatter, resources)
                if matched_resource:
                    match_type = "fuzzy"
            
            # Apply the match
            if matched_resource:
                matched_resource['knowledge_url'] = file_rel_path
                matched_resource['knowledge_hash'] = content_hash
                
                # Add resource_id to frontmatter if not present
                if not frontmatter.get('resource_id') and matched_resource.get('id'):
                    try:
                        _update_frontmatter_resource_id(md_file, matched_resource['id'])
                    except Exception as e:
                        logging.getLogger(__name__).warning(f"Failed to update frontmatter for {md_file}: {e}")
                
                result['linked'].append(f"{md_file.name}: linked to '{matched_resource.get('title', 'untitled')}' via {match_type}")
            else:
                result['skipped'].append(f"{md_file.name}: no matching resource found")
                
        # Save metadata if we made changes
        if result['linked'] or result['updated']:
            # Update the metadata.json file with the changes
            meta = load_metadata_file()
            meta_resources = meta.get('resources', [])
            
            # Update metadata resources with knowledge_url and knowledge_hash
            for resource in resources:
                if resource.get('knowledge_url') or resource.get('knowledge_hash'):
                    # Find corresponding metadata resource and update it
                    for meta_res in meta_resources:
                        if (resource.get('filename') and meta_res.get('filename') == resource.get('filename')) or \
                           (resource.get('url') and meta_res.get('url') == resource.get('url')):
                            if resource.get('knowledge_url'):
                                meta_res['knowledge_url'] = resource['knowledge_url']
                            if resource.get('knowledge_hash'):
                                meta_res['knowledge_hash'] = resource['knowledge_hash']
                            break
            
            save_metadata_file(meta)
            
    except Exception as e:
        result['conflicts'].append(f"Reconciliation error: {str(e)}")
        logging.getLogger(__name__).error(f"Reconciliation failed: {e}")
        
    return result


def _update_frontmatter_resource_id(md_file: Path, resource_id: str) -> None:
    """Add resource_id to frontmatter of markdown file"""
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter_yaml = parts[1].strip()
                body = parts[2]
                
                # Parse existing frontmatter
                frontmatter = yaml.safe_load(frontmatter_yaml) or {}
                frontmatter['resource_id'] = resource_id
                
                # Rebuild content
                new_frontmatter = yaml.safe_dump(frontmatter, default_flow_style=False).strip()
                new_content = f"---\n{new_frontmatter}\n---{body}"
                
                # Write atomically
                tmp_file = md_file.with_suffix(md_file.suffix + '.tmp')
                with open(tmp_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                os.replace(tmp_file, md_file)
                
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to update frontmatter for {md_file}: {e}")
        raise


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
        item = ResourceItem(
            title=m.get('title') or filename or 'Untitled',
            filename=filename,
            ext=ext,
            url=url or '',
            kind=kind,
            tags=m.get('tags', []),
            description=m.get('description'),
            uploaded_at=uploaded_dt,
            knowledge_url=m.get('knowledge_url')
        )
        # lazy thumbnail field (without generating)
        base_name = item.filename or (Path(item.url).name if item.url else None)
        if base_name:
            slug = Path(_safe_slug(Path(base_name).stem)).stem
            thumb_candidate = THUMBS_DIR / f"{slug}.jpg"
            if thumb_candidate.exists():
                item.thumbnail_url = f"/resources/bioweapons/thumbnails/{thumb_candidate.name}"
        meta_items.append(item)

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
        item = ResourceItem(
            title=p.name,
            filename=p.name,
            ext=ext,
            url=url,
            kind=kind,
            tags=[],
            description=None,
            uploaded_at=mtime
        )
        # pre-fill thumbnail if exists
        slug = Path(_safe_slug(p.stem)).stem
        thumb_candidate = THUMBS_DIR / f"{slug}.jpg"
        if thumb_candidate.exists():
            item.thumbnail_url = f"/resources/bioweapons/thumbnails/{thumb_candidate.name}"
        dir_items.append(item)
    return meta_items + dir_items

# -------------------------------------------------
# Research Sync helpers
# -------------------------------------------------
DEFAULT_FEEDS = [
    "https://pubmed.ncbi.nlm.nih.gov/rss/search/1G1RkJ2-example-spike-mitochondria/",
    "https://connect.medrxiv.org/relate/feed/181?custom=1&query=spike%20protein",
    "https://www.biorxiv.org/rss/subject/neuroscience.xml"
]


def normalize_entry(entry) -> Optional[ResearchArticle]:
    title = getattr(entry, 'title', None) or (entry.get('title') if isinstance(entry, dict) else None)
    link = getattr(entry, 'link', None) or (entry.get('link') if isinstance(entry, dict) else None)
    summary = getattr(entry, 'summary', None) or (entry.get('summary') if isinstance(entry, dict) else None)
    published_parsed = getattr(entry, 'published_parsed', None) or (entry.get('published_parsed') if isinstance(entry, dict) else None)
    published = date.today()
    if published_parsed:
        try:
            published = datetime(*published_parsed[:6], tzinfo=timezone.utc).date()
        except Exception:
            published = date.today()
    authors = []
    if hasattr(entry, 'authors'):
        try:
            authors = [a.get('name') for a in entry.authors if isinstance(a, dict) and a.get('name')]
        except Exception:
            authors = []
    doi = None
    if hasattr(entry, 'links'):
        for l in getattr(entry, 'links', []) or []:
            href = l.get('href') if isinstance(l, dict) else None
            if href and 'doi.org' in href:
                doi = href.split('doi.org/')[-1]
                break
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
            if resp.status_code != 200:
                raise Exception(f"status {resp.status_code}")
            parsed = feedparser.parse(resp.text)
            for entry in getattr(parsed, 'entries', [])[:50]:
                art = normalize_entry(entry)
                if not art:
                    continue
                total += 1
                q: Dict[str, str] = {}
                if art.doi:
                    q['doi'] = art.doi
                elif art.link:
                    q['link'] = art.link
                else:
                    q['title'] = art.title
                existing = db.articles.find_one(q)
                if existing:
                    db.articles.update_one(q, {"$set": prepare_for_mongo(art.model_dump())})
                    updated += 1
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
                db.articles.update_one(q, {"$set": prepare_for_mongo(art.model_dump())})
                updated += 1
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
    data = load_resources_from_folder_and_meta()
    # Generate thumbnails lazily (on request) for pdf/video if missing
    for r in data:
        if not r.thumbnail_url and (r.kind in ('pdf','video')):
            thumb = ensure_thumbnail_for_resource(r, prefer_time_sec=1.0)
            if thumb:
                r.thumbnail_url = thumb
    if tag:
        t = tag.lower()
        data = [r for r in data if any(t in (x.lower()) for x in (r.tags or []))]
    # try to auto-attach knowledge_url by reconciling with knowledge files
    try:
        _knowledge_reconcile_internal()
    except Exception:
        pass
    return data


@api.post("/resources/upload", response_model=TaskResponse, status_code=202)
async def upload_resource(
    file: UploadFile = File(...),
    title: Optional[str] = Form(default=None),
    tags: Optional[str] = Form(default=None),
    description: Optional[str] = Form(default=None),
    idempotency_key: Optional[str] = Header(default=None, alias="X-Idempotency-Key")
):
    try:
        # Generate idempotency key if not provided
        if not idempotency_key:
            idempotency_key = str(uuid.uuid4())
        
        # Check for existing task with same idempotency key
        existing_task = find_task_by_idempotency_key(idempotency_key)
        if existing_task:
            return TaskResponse(
                task_id=existing_task.task_id,
                idempotency_key=existing_task.idempotency_key,
                status=existing_task.status,
                message="Task already exists for this idempotency key"
            )
        
        # Validate file upload
        is_valid, error_message = validate_file_upload(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # Read file content
        file_content = await file.read()
        
        # Create task
        task_info = create_task(idempotency_key, file.filename)
        
        # Start background processing
        asyncio.create_task(process_upload_task(
            task_info.task_id, 
            file_content, 
            file.filename,
            title,
            tags,
            description
        ))
        
        return TaskResponse(
            task_id=task_info.task_id,
            idempotency_key=task_info.idempotency_key,
            status=TaskStatus.PENDING,
            message="Upload task created successfully"
        )
        
    except HTTPException:
        raise
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
        thumb_url = None
        temp_item = ResourceItem(
            title=entry['title'], filename=entry.get('filename'), ext=entry.get('ext'), url=entry.get('url'), kind=entry.get('kind'), tags=entry.get('tags', []), description=entry.get('description'), uploaded_at=datetime.fromisoformat(entry['uploaded_at'])
        )
        if temp_item.kind in ('pdf','video'):
            thumb_url = ensure_thumbnail_for_resource(temp_item)
        temp_item.thumbnail_url = thumb_url
        return temp_item
    r = resources[idx]
    if body.title is not None: r['title'] = body.title
    if body.description is not None: r['description'] = body.description
    if body.tags is not None: r['tags'] = body.tags
    meta['resources'] = resources
    save_metadata_file(meta)
    ext = r.get('ext') or (Path(r.get('filename') or '').suffix.lstrip('.') if r.get('filename') else None)
    kind = r.get('kind') or infer_kind_from_ext(ext or '')
    uploaded_at = r.get('uploaded_at') or datetime.now(timezone.utc).isoformat()
    temp_item = ResourceItem(
        title=r.get('title') or r.get('filename') or 'Untitled',
        filename=r.get('filename'),
        ext=ext,
        url=r.get('url') or '',
        kind=kind,
        tags=r.get('tags', []),
        description=r.get('description'),
        uploaded_at=datetime.fromisoformat(uploaded_at)
    )
    if temp_item.kind in ('pdf','video') and not temp_item.thumbnail_url:
        temp_item.thumbnail_url = ensure_thumbnail_for_resource(temp_item)
    return temp_item


@api.delete("/resources/delete")
async def delete_resource(filename: Optional[str] = Query(default=None), url: Optional[str] = Query(default=None)):
    if not filename and not url:
        raise HTTPException(status_code=400, detail="filename or url required")
    meta = load_metadata_file()
    resources = meta.get('resources', [])
    new_res = []
    removed = False
    for r in resources:
        if (filename and r.get('filename') == filename) or (url and r.get('url') == url):
            # try remove thumbnail too
            try:
                base = Path(filename or Path(url).name).stem if (filename or url) else None
                if base:
                    slug = Path(_safe_slug(base)).stem
                    thumb_path = THUMBS_DIR / f"{slug}.jpg"
                    if thumb_path.exists():
                        thumb_path.unlink()
            except Exception:
                pass
            removed = True
            continue
        new_res.append(r)
    meta['resources'] = new_res
    save_metadata_file(meta)
    if filename:
        try:
            p = PUBLIC_RESOURCES_DIR / Path(filename).name
            if p.exists():
                p.unlink()
        except Exception:
            pass
    return {"ok": True, "removed": removed}

# -------------------------
# Knowledge Endpoints
# -------------------------

def _knowledge_reconcile_internal() -> int:
    meta = load_metadata_file()
    resources = meta.get('resources', [])
    # Build map: slug -> list of resource dicts
    def mk_slug(s: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_\-]+","-", (s or '').lower()).strip('-')
    res_map: Dict[str, List[dict]] = {}
    for r in resources:
        title = r.get('title') or r.get('filename') or r.get('url') or ''
        slug = mk_slug(Path(title).stem)
        res_map.setdefault(slug, []).append(r)
    updated = 0
    for p in KNOWLEDGE_DIR.glob('*.md'):
        name = p.stem
        base = re.sub(r"-(\d+)$", "", name).replace('_video','')
        if base in res_map:
            for r in res_map[base]:
                if not r.get('knowledge_url'):
                    r['knowledge_url'] = f"/knowledge/{p.name}"
                    updated += 1
    if updated:
        meta['resources'] = resources
        save_metadata_file(meta)
    return updated

@api.get("/knowledge/status")
async def knowledge_status():
    files = []
    for p in sorted(KNOWLEDGE_DIR.glob("*.md")):
        st = p.stat()
        files.append({
            "filename": p.name,
            "url": f"/knowledge/{p.name}",
            "modified": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
            "size": st.st_size
        })
    return {"files": files}

@api.post("/knowledge/reconcile")
async def knowledge_reconcile() -> ReconcileResult:
    """Advanced reconciliation with hash-based matching and detailed reporting"""
    return advanced_knowledge_reconcile()


@api.get("/knowledge/task_status")
async def get_task_status(task_id: str = Query(...)):
    """Get the status of an upload task"""
    task_info = get_task(task_id)
    if not task_info:
        raise HTTPException(status_code=404, detail="Task not found")
    
    response_data = {
        "task_id": task_info.task_id,
        "idempotency_key": task_info.idempotency_key,
        "status": task_info.status,
        "created_at": task_info.created_at.isoformat(),
        "updated_at": task_info.updated_at.isoformat()
    }
    
    if task_info.resource_filename:
        response_data["resource_filename"] = task_info.resource_filename
        
    if task_info.resource_url:
        response_data["resource_url"] = task_info.resource_url
        
    if task_info.result:
        response_data["result"] = task_info.result.model_dump()
        
    if task_info.error_message:
        response_data["error_message"] = task_info.error_message
        
    return response_data

# -------------------------------------------------
# Other routes
# -------------------------------------------------
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

# -------------------------
# Local AI endpoints
# -------------------------
@api.post("/ai/summarize_local", response_model=AISummaryResponse)
async def ai_summarize_local(body: AISummaryRequest):
    text = (body.text or '').strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    summary, key_points = summarize_text(text, max_sentences=max(1, min(8, body.max_sentences)))
    return AISummaryResponse(summary=summary, key_points=key_points)


@api.post("/ai/answer_local", response_model=AIAnswerResponse)
async def ai_answer_local(body: AIAnswerRequest):
    await ensure_seed()
    q = (body.question or '').strip()
    if not q:
        raise HTTPException(status_code=400, detail="question is required")
    scopes = set((body.scope or ['research','resources','treatments','feed']))
    docs: List[Tuple[str, str, Optional[str], str]] = []
    if 'research' in scopes:
        arts = await db.articles.find({}).to_list(200)
        for a in arts:
            a2 = parse_from_mongo(a)
            docs.append(('research', a2.get('title',''), a2.get('link'), f"{a2.get('title','')}. {a2.get('abstract','') or ''}"))
    if 'resources' in scopes:
        res = await db.resources.find({}).to_list(200)
        for r in res:
            r2 = parse_from_mongo(r)
            docs.append(('resource', r2.get('title',''), r2.get('url'), f"{r2.get('title','')}. {r2.get('description','') or ''}"))
    if 'treatments' in scopes:
        trs = await db.treatments.find({}).to_list(200)
        for t in trs:
            t2 = parse_from_mongo(t)
            mech = "; ".join(t2.get('mechanisms', []) or [])
            docs.append(('treatment', t2.get('name',''), None, f"{t2.get('name','')}. {mech}"))
    if 'feed' in scopes:
        fds = await db.feed.find({}).to_list(200)
        for f in fds:
            f2 = parse_from_mongo(f)
            docs.append(('feed', f2.get('title',''), f2.get('url'), f"{f2.get('title','')}. {f2.get('summary','') or ''}"))

    kw = extract_keywords(q)
    def score(text: str) -> float:
        toks = tokenize(text)
        if not toks: return 0.0
        s = sum(1.0 for k in kw if k in toks)
        for k in kw:
            s += 0.2 * toks.count(k)
        return s / math.sqrt(len(toks) + 1)

    scored: List[Tuple[float, Tuple[str,str,Optional[str],str]]] = []
    for d in docs:
        sc = score(d[3])
        if sc > 0: scored.append((sc, d))
    top = [d for _, d in sorted(scored, key=lambda x: x[0], reverse=True)[:3]]

    if not top:
        return AIAnswerResponse(answer="I could not find relevant items locally. Try refining your question.", references=[])

    combined = "\n\n".join(t[3] for t in top)
    summary, _ = summarize_text(combined, max_sentences=5)
    refs = [AIAnswerReference(title=t[1], link=t[2], type=t[0]) for t in top]
    return AIAnswerResponse(answer=summary, references=refs)

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