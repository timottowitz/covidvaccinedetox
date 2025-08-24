import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { useSearchParams } from 'react-router-dom';
import { copyWithFeedback } from '../utils/clipboard';
import { Copy, CheckCircle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function KnowledgeList(){
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(null);
  const [md, setMd] = useState('');
  const [searchParams, setSearchParams] = useSearchParams();
  const [copyStates, setCopyStates] = useState({});  // Track copy button states

  const load = async () => {
    setLoading(true);
    try{
      const { data } = await axios.get(`${API}/knowledge/status`);
      setFiles(data.files || []);
    } finally { setLoading(false); }
  };

  const parseFrontmatter = (text) => {
    if (!text.startsWith('---')) return { meta: null, body: text };
    const end = text.indexOf('\n---');
    if (end === -1) return { meta: null, body: text };
    const raw = text.substring(3, end).trim();
    const body = text.substring(end + 4).trimStart();
    const meta = {};
    raw.split('\n').forEach(line => {
      const idx = line.indexOf(':');
      if (idx > -1) {
        const k = line.substring(0, idx).trim();
        const v = line.substring(idx + 1).trim();
        meta[k] = v.replace(/^"|"$/g, '');
      }
    });
    return { meta, body };
  };

  const open = async (f) => {
    setSelected(f);
    try{
      const res = await fetch(f.url);
      let txt = await res.text();
      // Anchor IDs: add id="c-N" to headings like "### Chunk N"
      txt = txt.replace(/###\s+Chunk\s+(\d+)\s*\(([^)]+)\)/g, (m, idx, rest) => `### Chunk ${idx} (${rest})\n<a id="c-${idx}"></a>`);
      const { meta, body } = parseFrontmatter(txt);
      setMd(body);
      setSelected({ ...f, meta });
      // Update URL search param for deep link
      const next = new URLSearchParams(searchParams);
      next.set('open', f.filename);
      setSearchParams(next);
    } catch {
      setMd('# Failed to load');
    }
  };
  
  // Enhanced copy functions with visual feedback
  const handleCopy = async (text, type) => {
    const key = `${selected.filename}-${type}`;
    
    const result = await copyWithFeedback(text, {
      successMessage: `${type} copied!`,
      errorMessage: `Failed to copy ${type.toLowerCase()}`
    });
    
    if (result.success) {
      // Show success state
      setCopyStates(prev => ({ ...prev, [key]: 'success' }));
      
      // Reset after 2 seconds
      setTimeout(() => {
        setCopyStates(prev => ({ ...prev, [key]: null }));
      }, 2000);
    } else {
      // Show error state briefly
      setCopyStates(prev => ({ ...prev, [key]: 'error' }));
      
      setTimeout(() => {
        setCopyStates(prev => ({ ...prev, [key]: null }));
      }, 3000);
    }
  };

  useEffect(()=>{ load(); },[]);

  return (
    <div className="container">
      <div className="grid">
        <Card className="card" style={{gridColumn:'span 12'}}>
          <CardHeader>
            <CardTitle className="card-title">Knowledge</CardTitle>
          </CardHeader>
          <CardContent>
            <div style={{display:'flex',gap:12,alignItems:'center',flexWrap:'wrap'}}>
              <Button onClick={load} disabled={loading}>{loading ? 'Refreshing…' : 'Refresh'}</Button>
            </div>
          </CardContent>
        </Card>

        <div style={{display:'grid', gridTemplateColumns:'320px 1fr', gap:16, gridColumn:'span 12'}}>
          <div style={{display:'flex',flexDirection:'column',gap:8}}>
            {(files||[]).map((f,idx)=> (
              <Card key={idx} className="card" onClick={()=>open(f)} style={{cursor:'pointer'}}>
                <CardHeader>
                  <CardTitle className="card-title" style={{fontSize:16}}>{f.filename}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="card-meta">{new Date(f.modified).toLocaleString()} • {(f.size/1024).toFixed(1)} KB</div>
                  <div style={{display:'flex',gap:8,marginTop:8,flexWrap:'wrap'}}>
                    {/* Quick anchors for chunks 1..5 if present */}
                    {[1,2,3,4,5].map(n => (
                      <Button key={n} variant="outline" size="sm" onClick={(e)=>{e.stopPropagation(); if(selected?.filename!==f.filename) {open(f).then(()=> setTimeout(()=>{document.getElementById(`c-${n}`)?.scrollIntoView({behavior:'smooth', block:'start'});},400));} else {document.getElementById(`c-${n}`)?.scrollIntoView({behavior:'smooth', block:'start'});} }}>Chunk {n}</Button>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          <div>
            {selected ? (
              <Card className="card">
                <CardHeader>
                  <CardTitle className="card-title">{selected.meta?.title || selected.filename}</CardTitle>
                  <div className="card-meta">
                    {selected.meta?.date && <span style={{marginRight:8}}>{new Date(selected.meta.date).toLocaleDateString()}</span>}
                    {selected.meta?.type && <span className="tag">{selected.meta.type}</span>}
                    {selected.meta?.tags && <>
                      {String(selected.meta.tags).split(',').map((t,i)=>(<span key={i} className="tag">{t.trim()}</span>))}
                    </>}
                  </div>
                  {selected.meta?.summary && <p style={{marginTop:8}}>{selected.meta.summary}</p>}
                </CardHeader>
                <CardContent>
                  <div style={{display:'flex', gap:8, flexWrap:'wrap', marginBottom:8}}>
                    {/* Copy summary button */}
                    {selected.meta?.summary && (
                      <Button size="sm" variant="outline" onClick={()=>{navigator.clipboard.writeText(selected.meta.summary)}}>Copy Summary</Button>
                    )}
                    {/* Copy citation */}
                    <Button size="sm" variant="outline" onClick={()=>{
                      const title = selected.meta?.title || selected.filename;
                      const date = selected.meta?.date || '';
                      const cite = `${title} — ${date} — ${window.location.origin}${selected.url || selected.href || selected.path || ''}`;
                      navigator.clipboard.writeText(cite);
                    }}>Copy Citation</Button>
                  </div>
                  <div className="prose" style={{maxWidth:'100%'}}>
                    <ReactMarkdown>{md}</ReactMarkdown>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card className="card">
                <CardContent>
                  <div className="card-meta">Select a knowledge file to preview</div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}