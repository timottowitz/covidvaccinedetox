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

// ... header and other components above unchanged in this patch ...

function ResourceIcon({kind}){
  if(kind === 'pdf') return <span>PDF</span>
  if(kind === 'video') return <span>VID</span>
  if(kind === 'audio') return <span>AUD</span>
  return <span>FILE</span>
}

function ResourceCard({r}){
  return (
    <Card className="card fade-in">
      <CardHeader>
        <CardTitle className="card-title" style={{display:'flex',gap:8,alignItems:'center'}}>
          <ResourceIcon kind={r.kind} /> {r.title}
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
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState("");
  const [tags, setTags] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if(!file){ toast({title:'Select a file first'}); return; }
    try{
      setBusy(true);
      const fd = new FormData();
      fd.append('file', file);
      if(title) fd.append('title', title);
      if(tags) fd.append('tags', tags);
      if(description) fd.append('description', description);
      await api.post('/resources/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      toast({title:'Uploaded', description:'Resource added'});
      setFile(null); setTitle(""); setTags(""); setDescription("");
      onDone && onDone();
    } catch(e){
      toast({title:'Upload failed', description:'Please try again'});
    } finally { setBusy(false); }
  };

  return (
    <Card className="card" style={{gridColumn:'span 12'}}>
      <CardHeader>
        <CardTitle className="card-title">Add a resource</CardTitle>
      </CardHeader>
      <CardContent>
        <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:12}}>
          <div>
            <Input type="file" onChange={e=> setFile(e.target.files?.[0] || null)} />
          </div>
          <Input placeholder="Title (optional)" value={title} onChange={e=>setTitle(e.target.value)} />
          <Input placeholder="Tags (comma-separated)" value={tags} onChange={e=>setTags(e.target.value)} />
          <Textarea placeholder="Description (optional)" value={description} onChange={e=>setDescription(e.target.value)} rows={3} />
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
      {/* Header defined earlier in file */}
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

          {items.map(r => <ResourceCard key={r.id + r.url} r={r} />)}
        </div>
      </div>
      <Toaster />
    </>
  )
}

// Note: App Router wiring and other pages exist earlier; ensure /resources route is present