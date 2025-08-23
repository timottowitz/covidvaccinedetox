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

function Research(){
  const api = useApi();
  const [articles, setArticles] = useState([]);
  const [openId, setOpenId] = useState(null);
  const [summ, setSumm] = useState({});
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

  const doSummarize = async (a) => {
    try {
      setOpenId(a.id);
      setSumm(prev => ({...prev, [a.id]: {loading:true}}));
      const text = `${a.title}. ${a.abstract || ''}`;
      const {data} = await api.post('/ai/summarize_local', {text, max_sentences: 4});
      setSumm(prev => ({...prev, [a.id]: data}));
    } catch(e){
      setSumm(prev => ({...prev, [a.id]: {error: true}}));
      toast({title:'Summary failed', description:'Please try again'});
    }
  };

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
                <div className="card-actions" style={{display:'flex', gap:12, flexWrap:'wrap'}}>
                  {a.link && <a className="pill" href={a.link} target="_blank" rel="noreferrer">View Paper <ExternalLink size={16} style={{marginLeft:8}}/></a>}
                  <Button onClick={()=>doSummarize(a)}>Summarize</Button>
                  <Dialog open={openId===a.id} onOpenChange={(o)=>{ if(!o) setOpenId(null); }}>
                    <DialogTrigger asChild>
                      <span></span>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Summary</DialogTitle>
                      </DialogHeader>
                      {summ[a.id]?.loading && <div className="card-meta">Generating summary…</div>}
                      {summ[a.id]?.error && <div className="card-meta">Failed to summarize.</div>}
                      {summ[a.id]?.summary && (
                        <div>
                          <p style={{marginBottom:8}}>{summ[a.id].summary}</p>
                          {summ[a.id].key_points?.length>0 && (
                            <ul style={{marginTop:6, paddingLeft:18}}>
                              {summ[a.id].key_points.map((k,i)=>(<li key={i}>{k}</li>))}
                            </ul>
                          )}
                        </div>
                      )}
                    </DialogContent>
                  </Dialog>
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

// Media, Resources, Treatments, Shop components were added previously and remain available

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/research" element={<Research />} />
          {/* Other routes exist in file from earlier steps: /media, /resources, /treatments, /shop */}
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;