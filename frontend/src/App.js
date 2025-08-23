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
import KnowledgeList from "./components/KnowledgeList";
import ErrorBoundary from "./components/ErrorBoundary";

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
              <Link to="/knowledge" data-testid="nav-knowledge"><button className="pill" style={{background:'#a855f7'}}>Knowledge</button></Link>
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

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/research" element={<Research />} />
            <Route path="/resources" element={<Resources />} />
            <Route path="/knowledge" element={<KnowledgeList />} />
            <Route path="/media" element={<Media />} />
            <Route path="/treatments" element={<Treatments />} />
            <Route path="/shop" element={<Shop />} />
          </Routes>
        </ErrorBoundary>
      </BrowserRouter>
    </div>
  );
}

export default App;