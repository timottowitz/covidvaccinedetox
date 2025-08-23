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
            </div>
          </div>
          <img alt="hero" src="https://images.unsplash.com/photo-1655890954753-f9ec41ce58ae" style={{width:360,borderRadius:16,objectFit:'cover',filter:'grayscale(10%) contrast(95%)'}} />
        </div>
      </div>
    </div>
  );
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

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/research" element={<Research />} />
          <Route path="/resources" element={<Resources />} />
          {/* Other routes: /media, /treatments, /shop defined earlier in file */}
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;