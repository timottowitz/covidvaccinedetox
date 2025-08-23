import { useEffect, useMemo, useState } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, useSearchParams } from "react-router-dom";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
import { Input } from "./components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Toaster } from "./components/ui/toaster";
import { toast } from "./hooks/use-toast";
import { Calendar } from "./components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "./components/ui/popover";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "./components/ui/dialog";
import { CalendarIcon, ShoppingCart, ExternalLink, FileText, Video, AudioLines, Download } from "lucide-react";

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
  if(kind === 'pdf') return <FileText size={16} />
  if(kind === 'video') return <Video size={16} />
  if(kind === 'audio') return <AudioLines size={16} />
  return <FileText size={16} />
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
          <Dialog>
            <DialogTrigger asChild>
              <button className="pill"><ExternalLink size={16} style={{marginRight:8}}/> Preview</button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{r.title}</DialogTitle>
              </DialogHeader>
              <div style={{height:420}}>
                {r.kind === 'pdf' && (
                  <iframe title="pdf" src={r.url} style={{border:'1px solid #e2e8f0', width:'100%', height:'100%', borderRadius:12}} />
                )}
                {r.kind === 'video' && (
                  <video controls style={{width:'100%', height:'100%', objectFit:'cover', borderRadius:12}} src={r.url} />
                )}
                {r.kind === 'audio' && (
                  <audio controls style={{width:'100%'}} src={r.url} />
                )}
              </div>
              <div style={{display:'flex',gap:12,marginTop:12}}>
                <a className="pill" href={r.url} target="_blank" rel="noreferrer"><Download size={16} style={{marginRight:8}}/>Download</a>
              </div>
            </DialogContent>
          </Dialog>
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

  useEffect(() => { (async () => {
    try {
      const {data} = await api.get(`/resources${tag ? `?tag=${encodeURIComponent(tag)}`: ''}`);
      setItems(data);
    } catch (e) {
      toast({title:'Load failed', description:'Could not load resources'});
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
                <Input placeholder="Filter by tag (e.g., spike protein)" value={tag} onChange={e => setSearchParams({tag: e.target.value})} style={{maxWidth:280}} />
              </div>
            </CardContent>
          </Card>
          {items.map(r => <ResourceCard key={r.id} r={r} />)}
        </div>
      </div>
      <Toaster />
    </>
  )
}

function Treatments(){
  const api = useApi();
  const [items, setItems] = useState([]);
  const [searchParams, setSearchParams] = useSearchParams();
  const tag = searchParams.get('tag') || '';

  useEffect(() => { (async () => {
    try {
      const {data} = await api.get(`/treatments${tag ? `?tag=${encodeURIComponent(tag)}`: ''}`);
      setItems(data);
    } catch (e) {
      toast({title:'Load failed', description:'Could not load treatments'});
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
                <Input placeholder="Filter by tag (e.g., NAC)" value={tag} onChange={e => setSearchParams({tag: e.target.value})} style={{maxWidth:260}} />
              </div>
            </CardContent>
          </Card>

          {items.map(t => (
            <Card key={t.id} className="card fade-in">
              <CardHeader>
                <CardTitle className="card-title">{t.name}</CardTitle>
                <div className="card-meta">{(t.tags||[]).map(x => <span key={x} className="tag">{x}</span>)}</div>
              </CardHeader>
              <CardContent>
                <div style={{marginBottom:8}}>
                  <strong>Mechanisms:</strong>
                  <ul style={{marginTop:8, paddingLeft:18}}>
                    {(t.mechanisms||[]).map((m,i) => <li key={i} style={{marginBottom:4}}>{m}</li>)}
                  </ul>
                </div>
                {t.dosage && <p style={{marginBottom:4}}><strong>Dosage:</strong> {t.dosage}</p>}
                {t.duration && <p style={{marginBottom:8}}><strong>Duration:</strong> {t.duration}</p>}
                <div style={{display:'flex', gap:12, flexWrap:'wrap'}}>
                  {(t.links||[]).map((l,i) => <a key={i} className="pill" href={l} target="_blank" rel="noreferrer">Study <ExternalLink size={16} style={{marginLeft:8}}/></a>)}
                  {t.bundle_product && (
                    <Link to="/shop" className="pill">View Bundle <ShoppingCart size={16} style={{marginLeft:8}}/></Link>
                  )}
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
          <Route path="/treatments" element={<Treatments />} />
          <Route path="/shop" element={<Shop />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;