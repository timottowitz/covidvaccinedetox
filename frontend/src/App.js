import { useEffect, useMemo, useState } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, useSearchParams } from "react-router-dom";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
import { Input } from "./components/ui/input";
import { Textarea } from "./components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Toaster } from "./components/ui/toaster";
import { toast } from "./hooks/use-toast";
import { Calendar } from "./components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "./components/ui/popover";
import { Button } from "./components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "./components/ui/dialog";
import { AspectRatio } from "./components/ui/aspect-ratio";
import { CalendarIcon, ShoppingCart, ExternalLink } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function useApi() {
  const client = useMemo(() => axios.create({ baseURL: API }), []);
  return client;
}

function AskDialog(){
  const api = useApi();
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [answer, setAnswer] = useState(null);
  const submit = async () => {
    if(!q.trim()) return;
    try {
      setAnswer({loading:true});
      const {data} = await api.post('/ai/answer_local', {question: q});
      setAnswer(data);
    } catch(e){
      toast({title:'Answer failed', description:'Try refining your question'});
    }
  };
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <button className="pill" style={{background:'#111827'}}>Ask</button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Ask about spike protein or treatments</DialogTitle>
        </DialogHeader>
        <Textarea placeholder="Type your question..." value={q} onChange={e=>setQ(e.target.value)} rows={4} />
        <div style={{display:'flex', gap:12}}>
          <Button onClick={submit}>Get Answer</Button>
        </div>
        {answer && (
          <div style={{marginTop:12}}>
            {answer.loading ? (
              <div className="card-meta">Thinking...</div>
            ) : (
              <>
                <p style={{marginBottom:8}}>{answer.answer}</p>
                {(answer.references||[]).length > 0 && (
                  <div>
                    <strong>References</strong>
                    <ul style={{marginTop:6, paddingLeft:18}}>
                      {answer.references.map((r,i)=> (
                        <li key={i}><a href={r.link || '#'} target="_blank" rel="noreferrer">[{r.type}] {r.title}</a></li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

function Header() {
  return (
    <div className="container">
      <div className="hero fade-in">
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:16,flexWrap:'wrap'}}>
          <div>
            <h1>mRNA Vaccine Knowledge Base</h1>
            <p>Curated research on spike protein, treatments, and media. Updated continuously.</p>
            <div className="nav" style={{marginTop:16}}>
              <Link to="/"><button className="pill">Home</button></Link>
              <Link to="/research" data-testid="nav-research"><button className="pill" style={{background:'#0ea5a5'}}>Research</button></Link>
              <Link to="/resources" data-testid="nav-resources"><button className="pill" style={{background:'#10b981'}}>Resources</button></Link>
              <Link to="/media" data-testid="nav-media"><button className="pill" style={{background:'#2563eb'}}>Media</button></Link>
              <Link to="/treatments" data-testid="nav-treatments"><button className="pill" style={{background:'#475569'}}>Treatments</button></Link>
              <Link to="/shop" data-testid="nav-shop"><button className="pill" style={{background:'#0284c7'}}>Shop</button></Link>
              <AskDialog />
            </div>
          </div>
          <img alt="hero" src="https://images.unsplash.com/photo-1655890954753-f9ec41ce58ae" style={{width:360,borderRadius:16,objectFit:'cover',filter:'grayscale(10%) contrast(95%)'}} />
        </div>
      </div>
    </div>
  );
}

function FeedCard({item}){
  return (
    <Card className="card fade-in">
      <CardHeader>
        <CardTitle className="card-title">{item.title}</CardTitle>
        <div className="card-meta">{item.source || item.type} • {new Date(item.published_at).toLocaleDateString()}</div>
      </CardHeader>
      <CardContent>
        <p>{item.summary}</p>
        <div style={{marginTop:12}}>
          {item.tags?.slice(0,5).map(t => <span className="tag" key={t}>#{t}</span>)}
        </div>
        <div className="card-actions">
          <a className="pill" href={item.url} target="_blank" rel="noreferrer">Open <ExternalLink size={16} style={{marginLeft:8}}/></a>
        </div>
      </CardContent>
    </Card>
  )
}

function Home(){
  const api = useApi();
  const [feed, setFeed] = useState([]);
  const [tag, setTag] = useState("");

  useEffect(() => { (async () => {
    try {
      await api.get("/");
      const {data} = await api.get(`/feed${tag ? `?tag=${encodeURIComponent(tag)}`: ''}`);
      setFeed(data);
    } catch (e) {
      toast({title: "Network error", description: "Could not load feed"});
    }
  })(); }, [tag]);

  return (
    <>
      <Header />
      <div className="container">
        <div className="grid">
          <Card className="card" style={{gridColumn:'span 12'}}>
            <CardContent>
              <div style={{display:'flex', gap:12, alignItems:'center', flexWrap:'wrap'}}>
                <Input placeholder="Filter by tag (e.g., spike)" value={tag} onChange={e => setTag(e.target.value)} style={{maxWidth:260}} />
                <Popover>
                  <PopoverTrigger asChild>
                    <button className="pill" aria-label="Pick a date"><CalendarIcon size={16} style={{marginRight:8}}/>Date</button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar mode="single" selected={undefined} />
                  </PopoverContent>
                </Popover>
              </div>
            </CardContent>
          </Card>
          {feed.map(item => <FeedCard key={item.id} item={item} />)}
        </div>
      </div>
      <Toaster />
    </>
  )
}

function Research(){
  const api = useApi();
  const [articles, setArticles] = useState([]);
  const [searchParams, setSearchParams] = useSearchParams();
  const tag = searchParams.get('tag') || '';
  const sort = searchParams.get('sort') || 'date';
  const [syncing, setSyncing] = useState(false);

  const refresh = async () => {
    try {
      setSyncing(true);
      const { data } = await api.get('/research/sync');
      toast({ title: 'Research synced', description: `Added: ${data.added}, Updated: ${data.updated}`});
      const res = await api.get(`/research?sort_by=${encodeURIComponent(sort)}${tag ? `&tag=${encodeURIComponent(tag)}`: ''}`);
      setArticles(res.data);
    } catch (e) {
      toast({ title: 'Sync failed', description: 'Using last cached articles' });
    } finally { setSyncing(false); }
  };

  useEffect(() => { (async () => {
    try {
      const {data} = await api.get(`/research?sort_by=${encodeURIComponent(sort)}${tag ? `&tag=${encodeURIComponent(tag)}`: ''}`);
      setArticles(data);
    } catch (e) {
      toast({title:'Load failed', description:'Could not load research articles'});
    }
  })(); }, [tag, sort]);

  return (
    <>
      <Header />
      <div className="container">
        <div className="grid">
          <Card className="card" style={{gridColumn:'span 12'}}>
            <CardContent>
              <div style={{display:'flex', gap:12, alignItems:'center', flexWrap:'wrap'}}>
                <Input placeholder="Filter by tag (e.g., #spike)" value={tag} onChange={e => setSearchParams({tag: e.target.value, sort})} style={{maxWidth:260}} />
                <Select value={sort} onValueChange={(v) => setSearchParams({tag, sort: v})}>
                  <SelectTrigger style={{width:200}}>
                    <SelectValue placeholder="Sort by" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="date">Newest</SelectItem>
                    <SelectItem value="citations">Citations</SelectItem>
                  </SelectContent>
                </Select>
                <Button variant="default" disabled={syncing} onClick={refresh}>{syncing ? 'Syncing…' : 'Refresh Feed'}</Button>
              </div>
            </CardContent>
          </Card>

          {articles.map(a => (
            <Card key={a.id} className="card fade-in">
              <CardHeader>
                <CardTitle className="card-title">{a.title}</CardTitle>
                <div className="card-meta">{(a.authors||[]).join(', ')} • {new Date(a.published_date).toLocaleDateString()}</div>
              </CardHeader>
              <CardContent>
                <p style={{marginBottom:8}}>{a.abstract}</p>
                <div style={{marginBottom:12}}>
                  {(a.tags||[]).map(t => <span key={t} className="tag">{t}</span>)}
                </div>
                <div className="card-actions">
                  {a.link && <a className="pill" href={a.link} target="_blank" rel="noreferrer">View Paper <ExternalLink size={16} style={{marginLeft:8}}/></a>}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
      <Toaster />
    </>
  )
}

function ResourceIcon({kind}){
  if(kind === 'pdf') return <span>PDF</span>
  if(kind === 'video') return <span>VID</span>
  if(kind === 'audio') return <span>AUD</span>
  return <span>FILE</span>
}

function EditResourceDialog({r, onSaved, onDeleted}){
  const api = useApi();
  const [title, setTitle] = useState(r.title || '');
  const [tags, setTags] = useState((r.tags||[]).join(', '));
  const [description, setDescription] = useState(r.description || '');

  const save = async () => {
    try{
      const payload = { filename: r.filename || null, url: r.url, title, description, tags: tags.split(',').map(t=>t.trim()).filter(Boolean) };
      await api.patch('/resources/metadata', payload);
      toast({title:'Saved'});
      onSaved && onSaved();
    }catch(e){ toast({title:'Save failed', description:'Try again'}); }
  };

  const del = async () => {
    try{
      await api.delete('/resources/delete', { params: { filename: r.filename || undefined, url: r.url || undefined } });
      toast({title:'Deleted'});
      onDeleted && onDeleted();
    }catch(e){ toast({title:'Delete failed', description:'Try again'}); }
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">Edit</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit resource</DialogTitle>
        </DialogHeader>
        <Input placeholder="Title" value={title} onChange={e=>setTitle(e.target.value)} />
        <Input placeholder="Tags (comma separated)" value={tags} onChange={e=>setTags(e.target.value)} />
        <Textarea placeholder="Description" value={description} onChange={e=>setDescription(e.target.value)} rows={3} />
        <div style={{display:'flex', gap:12}}>
          <Button onClick={save}>Save</Button>
          <Button variant="destructive" onClick={del}>Delete</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function ResourceCard({r, onChanged}){
  return (
    <Card className="card fade-in">
      <CardHeader>
        <CardTitle className="card-title" style={{display:'flex',gap:8,alignItems:'center',justifyContent:'space-between'}}>
          <span style={{display:'flex',alignItems:'center',gap:8}}><ResourceIcon kind={r.kind} /> {r.title}</span>
          <EditResourceDialog r={r} onSaved={onChanged} onDeleted={onChanged} />
        </CardTitle>
        <div className="card-meta">{r.ext?.toUpperCase()} • {new Date(r.uploaded_at).toLocaleDateString()}</div>
      </CardHeader>
      <CardContent>
        {r.thumbnail_url && (
          <div style={{marginBottom:12}}>
            <AspectRatio ratio={16/9}>
              <img src={r.thumbnail_url} alt={r.title} style={{width:'100%', height:'100%', objectFit:'cover', borderRadius:8}} />
            </AspectRatio>
          </div>
        )}
        <p>{r.description}</p>
        <div style={{marginTop:12}}>
          {(r.tags||[]).map(t => <span key={t} className="tag">{t}</span>)}
        </div>
        <div className="card-actions">
          <a className="pill" href={r.url} target="_blank" rel="noreferrer">Open</a>
        </div>
      </CardContent>
    </Card>
  )
}

function Uploader({onDone}){
  const api = useApi();
  const [files, setFiles] = useState([]);
  const [title, setTitle] = useState("");
  const [tags, setTags] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if(!files.length){ toast({title:'Select file(s) first'}); return; }
    try{
      setBusy(true);
      for(const f of files){
        const fd = new FormData();
        fd.append('file', f);
        if(title) fd.append('title', title);
        if(tags) fd.append('tags', tags);
        if(description) fd.append('description', description);
        await api.post('/resources/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      }
      toast({title:'Uploaded', description:`${files.length} file(s) added`});
      setFiles([]); setTitle(""); setTags(""); setDescription("");
      onDone && onDone();
    } catch(e){
      toast({title:'Upload failed', description:'Please try again'});
    } finally { setBusy(false); }
  };

  return (
    <Card className="card" style={{gridColumn:'span 12'}}>
      <CardHeader>
        <CardTitle className="card-title">Add resources</CardTitle>
      </CardHeader>
      <CardContent>
        <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:12}}>
          <div>
            <Input type="file" multiple onChange={e=> setFiles(Array.from(e.target.files||[]))} />
          </div>
          <Input placeholder="Shared Title (optional)" value={title} onChange={e=>setTitle(e.target.value)} />
          <Input placeholder="Shared Tags (comma-separated)" value={tags} onChange={e=>setTags(e.target.value)} />
          <Textarea placeholder="Shared Description (optional)" value={description} onChange={e=>setDescription(e.target.value)} rows={3} />
        </div>
        <div style={{marginTop:12}}>
          <Button disabled={busy} onClick={submit}>{busy? 'Uploading…':'Upload'}</Button>
        </div>
      </CardContent>
    </Card>
  )
}

function Resources(){
  const api = useApi();
  const [items, setItems] = useState([]);
  const [searchParams, setSearchParams] = useSearchParams();
  const tag = searchParams.get('tag') || '';

  const load = async () => {
    const {data} = await api.get(`/resources${tag ? `?tag=${encodeURIComponent(tag)}`: ''}`);
    setItems(data);
  };

  useEffect(() => { (async () => {
    try { await load(); } catch(e){ toast({title:'Load failed', description:'Could not load resources'});} })(); }, [tag]);

  return (
    <>
      <Header />
      <div className="container">
        <div className="grid">
          <Card className="card" style={{gridColumn:'span 12'}}>
            <CardContent>
              <div style={{display:'flex', gap:12, alignItems:'center', flexWrap:'wrap'}}>
                <Input placeholder="Filter by tag (e.g., spike protein)" value={tag} onChange={e => setSearchParams({tag: e.target.value})} style={{maxWidth:280}} />
                <Button variant="outline" onClick={load}>Rescan</Button>
              </div>
            </CardContent>
          </Card>

          <Uploader onDone={load} />

          {items.map(r => <ResourceCard key={(r.filename || r.url)} r={r} onChanged={load} />)}
        </div>
      </div>
      <Toaster />
    </>
  )
}

function Media(){
  const api = useApi();
  const [items, setItems] = useState([]);
  const [searchParams, setSearchParams] = useSearchParams();
  const tag = searchParams.get('tag') || '';
  const source = searchParams.get('source') || '';

  useEffect(() => { (async () => {
    try {
      let query = '';
      if (tag) query += `tag=${encodeURIComponent(tag)}&`;
      if (source) query += `source=${encodeURIComponent(source)}&`;
      if (query) query = '?' + query.slice(0, -1);
      const {data} = await api.get(`/media${query}`);
      setItems(data);
    } catch (e) {
      toast({title:'Load failed', description:'Could not load media items'});
    }
  })(); }, [tag, source]);

  return (
    <>
      <Header />
      <div className="container">
        <div className="grid">
          <Card className="card" style={{gridColumn:'span 12'}}>
            <CardContent>
              <div style={{display:'flex', gap:12, alignItems:'center', flexWrap:'wrap'}}>
                <Input placeholder="Filter by tag (e.g., spike)" value={tag} onChange={e => setSearchParams({tag: e.target.value, source})} style={{maxWidth:260}} />
                <Select value={source} onValueChange={(v) => setSearchParams({tag, source: v})}>
                  <SelectTrigger style={{width:200}}>
                    <SelectValue placeholder="All Sources" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All Sources</SelectItem>
                    <SelectItem value="YouTube">YouTube</SelectItem>
                    <SelectItem value="Vimeo">Vimeo</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {items.map(item => (
            <Card key={item.id} className="card fade-in">
              <CardHeader>
                <CardTitle className="card-title">{item.title}</CardTitle>
                <div className="card-meta">{item.source} • {new Date(item.published_at).toLocaleDateString()}</div>
              </CardHeader>
              <CardContent>
                <div style={{marginBottom:12}}>
                  <AspectRatio ratio={16/9}>
                    <iframe 
                      src={item.url} 
                      title={item.title}
                      frameBorder="0" 
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                      allowFullScreen
                      style={{width:'100%', height:'100%', borderRadius:8}}
                    />
                  </AspectRatio>
                </div>
                {item.description && <p style={{marginBottom:8}}>{item.description}</p>}
                <div style={{marginBottom:12}}>
                  {(item.tags||[]).map(t => <span key={t} className="tag">#{t}</span>)}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
      <Toaster />
    </>
  )
}

function Shop(){
  const [shopError, setShopError] = useState(false);
  useEffect(() => {
    const s = document.createElement('script');
    s.src = 'https://cdn.shoprocket.io/js/widget.js';
    s.async = true;
    s.onload = () => {
      try {
        if (window.ShopRocket) {
          // @ts-ignore
          new window.ShopRocket({
            container: '#shoprocket-products',
            storeId: 'sr-covid-vaccine-detox-2024',
            theme: 'modern',
            showPrice: true,
            showRating: true,
            columns: 3,
            responsiveBreakpoint: 768
          });
        }
        if (window.ShopRocketCart) {
          // @ts-ignore
          new window.ShopRocketCart({
            container: '#shoprocket-cart',
            storeId: 'sr-covid-vaccine-detox-2024',
            position: 'right',
            theme: 'dark',
            showTotal: true,
            iconSize: 'large'
          });
        }
      } catch (e) {
        console.warn('Shop widget init failed', e);
        setShopError(true);
      }
    };
    s.onerror = () => setShopError(true);
    document.body.appendChild(s);

    return () => { try { document.body.removeChild(s); } catch(_){} };
  }, []);

  return (
    <>
      <Header />
      <div className="container">
        <div className="shop-embed">
          <h2 className="section-title" style={{marginBottom:16}}>Our Products</h2>
          {shopError && (
            <div style={{padding:12, background:'#fff8e1', border:'1px solid #fde68a', borderRadius:12, marginBottom:12}}>
              <strong style={{display:'block', marginBottom:6}}>Live shop widget could not load.</strong>
              <span>Showing sample products instead. We can wire the official ShopRocket widget once CDN access is permitted.</span>
            </div>
          )}
          <div id="shoprocket-products" data-store-id="sr-covid-vaccine-detox-2024"></div>
          <div id="shoprocket-cart" data-store-id="sr-covid-vaccine-detox-2024"></div>

          {shopError && (
            <div className="grid" style={{marginTop:16}}>
              {[{t:'Spike Clearance Bundle',p:79},{t:'Gut Healing Kit',p:65},{t:'IGG4 Regulation Guidebook',p:29}].map((x,idx) => (
                <Card key={idx} className="card">
                  <CardHeader>
                    <CardTitle className="card-title">{x.t}</CardTitle>
                    <div className="card-meta">${'{'}x.p{'}'}</div>
                  </CardHeader>
                  <CardContent>
                    <div className="card-actions">
                      <a className="pill" href="#" onClick={(e)=>{e.preventDefault(); toast({title:'Demo', description:'Cart available when ShopRocket loads'});}}><ShoppingCart size={16} style={{marginRight:8}}/>Add to Cart</a>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  )
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/research" element={<Research />} />
          <Route path="/resources" element={<Resources />} />
          <Route path="/media" element={<Media />} />
          <Route path="/treatments" element={<Treatments />} />
          <Route path="/shop" element={<Shop />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;