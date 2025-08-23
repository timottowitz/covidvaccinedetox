import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function KnowledgeList(){
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(null);
  const [md, setMd] = useState('');

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
      const txt = await res.text();
      const { meta, body } = parseFrontmatter(txt);
      setMd(body);
      setSelected({ ...f, meta });
    } catch {
      setMd('# Failed to load');
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
                </CardContent>
              </Card>
            ))}
          </div>
          <div>
            {selected ? (
              <Card className="card">
                <CardHeader>
                  <CardTitle className="card-title">{selected.filename}</CardTitle>
                </CardHeader>
                <CardContent>
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