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
import { CalendarIcon, ShoppingCart, ExternalLink, Search, Filter, FileText, Video, Eye } from "lucide-react";
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

// Missing component definitions
function Home() {
  return (
    <div className="App">
      <Header />
      <div className="container">
        <div className="grid">
          <Card className="card" style={{gridColumn:'span 12'}}>
            <CardHeader>
              <CardTitle className="card-title">Welcome to mRNA Vaccine Knowledge Base</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Navigate using the buttons above to explore research, resources, and knowledge.</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Research() {
  return (
    <div className="App">
      <Header />
      <div className="container">
        <div className="grid">
          <Card className="card" style={{gridColumn:'span 12'}}>
            <CardHeader>
              <CardTitle className="card-title">Research</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Research page content goes here.</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Resources() {
  const api = useApi();
  const [resources, setResources] = useState([]);
  const [filteredResources, setFilteredResources] = useState([]);
  const [filter, setFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [tagFilter, setTagFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadTasks, setUploadTasks] = useState(new Map());

  // Load resources from backend
  useEffect(() => {
    loadResources();
  }, []);

  // Enhanced filtering with type, tag, and text filters
  useEffect(() => {
    let filtered = resources;
    
    // Type filter
    if (typeFilter !== "all") {
      filtered = filtered.filter(r => r.kind?.toLowerCase() === typeFilter.toLowerCase());
    }
    
    // Tag filter  
    if (tagFilter !== "all") {
      filtered = filtered.filter(r => 
        r.tags?.some(tag => tag.toLowerCase().includes(tagFilter.toLowerCase()))
      );
    }
    
    // Text filter
    if (filter.trim()) {
      filtered = filtered.filter(r => 
        r.title?.toLowerCase().includes(filter.toLowerCase()) ||
        r.description?.toLowerCase().includes(filter.toLowerCase()) ||
        r.tags?.some(tag => tag.toLowerCase().includes(filter.toLowerCase())) ||
        r.meta?.title?.toLowerCase().includes(filter.toLowerCase()) ||
        r.meta?.summary?.toLowerCase().includes(filter.toLowerCase())
      );
    }
    
    setFilteredResources(filtered);
  }, [resources, filter, typeFilter, tagFilter]);

  const loadResources = async () => {
    try {
      setLoading(true);
      const { data } = await api.get('/resources');
      setResources(data || []);
    } catch (error) {
      console.error('Failed to load resources:', error);
      toast({title: 'Error', description: 'Failed to load resources'});
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['application/pdf', 'video/mp4', 'video/quicktime', 'video/webm'];
    if (!allowedTypes.includes(file.type)) {
      toast({title: 'Invalid file type', description: 'Only PDF, MP4, QuickTime, and WebM files are allowed'});
      return;
    }

    // Validate file size (100MB)
    const maxSize = 100 * 1024 * 1024;
    if (file.size > maxSize) {
      toast({title: 'File too large', description: 'File size must be less than 100MB'});
      return;
    }

    try {
      setUploading(true);
      
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', file.name);
      formData.append('description', `Uploaded ${file.type} file`);

      // Generate idempotency key
      const idempotencyKey = `upload-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      
      const { data } = await api.post('/resources/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'X-Idempotency-Key': idempotencyKey
        }
      });

      if (data.task_id) {
        // Track upload task
        const newTask = {
          task_id: data.task_id,
          filename: file.name,
          status: data.status,
          idempotency_key: data.idempotency_key
        };
        setUploadTasks(prev => new Map(prev.set(data.task_id, newTask)));
        
        toast({title: 'Upload started', description: `Processing ${file.name}...`});
        
        // Monitor task status
        monitorTask(data.task_id);
      }
    } catch (error) {
      console.error('Upload failed:', error);
      const message = error.response?.data?.detail || 'Upload failed';
      toast({title: 'Upload failed', description: message});
    } finally {
      setUploading(false);
      // Reset file input
      event.target.value = '';
    }
  };

  const monitorTask = async (taskId) => {
    const maxAttempts = 120; // 10 minutes max with 5s intervals
    let attempts = 0;
    let pollInterval = null;
    
    const checkStatus = async () => {
      try {
        const { data } = await api.get(`/knowledge/task_status?task_id=${taskId}`);
        
        setUploadTasks(prev => {
          const newMap = new Map(prev);
          const task = newMap.get(taskId);
          if (task) {
            task.status = data.status;
            task.progress = data.progress || task.progress;
            task.stage = data.stage || task.stage;
            if (data.result) {
              task.result = data.result;
            }
            if (data.error_message) {
              task.error_message = data.error_message;
            }
            newMap.set(taskId, task);
          }
          return newMap;
        });

        if (data.status === 'completed') {
          if (pollInterval) clearInterval(pollInterval);
          
          toast({
            title: 'Upload completed', 
            description: `${data.result?.title || 'File'} processed successfully`
          });
          
          // Reload resources to show the new one
          loadResources();
          
          // Keep completed task visible for 10 seconds before removing
          setTimeout(() => {
            setUploadTasks(prev => {
              const newMap = new Map(prev);
              newMap.delete(taskId);
              return newMap;
            });
          }, 10000);
          return;
        } else if (data.status === 'failed') {
          if (pollInterval) clearInterval(pollInterval);
          
          toast({
            title: 'Upload failed', 
            description: data.error_message || 'Processing failed'
          });
          
          // Keep failed task visible for 15 seconds for user to see error
          setTimeout(() => {
            setUploadTasks(prev => {
              const newMap = new Map(prev);
              newMap.delete(taskId);
              return newMap;
            });
          }, 15000);
          return;
        }

        // Continue monitoring if still processing
        attempts++;
        if (attempts >= maxAttempts) {
          if (pollInterval) clearInterval(pollInterval);
          toast({
            title: 'Upload timeout', 
            description: 'Upload is taking longer than expected. Please check back later.'
          });
        }
      } catch (error) {
        console.error('Failed to check task status:', error);
        attempts++;
        
        if (attempts >= 5) { // Stop after 5 consecutive failures
          if (pollInterval) clearInterval(pollInterval);
          toast({
            title: 'Monitoring error', 
            description: 'Unable to check upload status. Please refresh the page.'
          });
        }
      }
    };

    // Initial check after 1 second
    setTimeout(checkStatus, 1000);
    
    // Then poll every 5 seconds
    setTimeout(() => {
      pollInterval = setInterval(checkStatus, 5000);
    }, 1000);
  };

  const openKnowledge = (resource) => {
    if (resource.knowledge_url) {
      // Navigate to knowledge page with the specific file
      window.location.href = `/knowledge?open=${encodeURIComponent(resource.knowledge_url.split('/').pop())}`;
    }
  };

  return (
    <div className="App">
      <Header />
      <div className="container">
        <div className="grid">
          <Card className="card" style={{gridColumn:'span 12'}}>
            <CardHeader>
              <CardTitle className="card-title">Resources</CardTitle>
            </CardHeader>
            <CardContent>
              {/* Enhanced Filtering */}
              <div style={{marginBottom: 16}}>
                <div style={{display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap', marginBottom: 12}}>
                  <div style={{flex: 1, minWidth: '250px', position: 'relative'}}>
                    <Search size={16} style={{position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#64748b'}} />
                    <Input 
                      placeholder="Search titles, descriptions, tags..." 
                      value={filter}
                      onChange={(e) => setFilter(e.target.value)}
                      style={{paddingLeft: 36}}
                    />
                  </div>
                  
                  <Select value={typeFilter} onValueChange={setTypeFilter}>
                    <SelectTrigger style={{width: 140}}>
                      <Filter size={16} style={{marginRight: 6}} />
                      <SelectValue placeholder="Type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Types</SelectItem>
                      <SelectItem value="pdf">
                        <div style={{display: 'flex', alignItems: 'center', gap: 6}}>
                          <FileText size={14} />
                          PDF
                        </div>
                      </SelectItem>
                      <SelectItem value="video">
                        <div style={{display: 'flex', alignItems: 'center', gap: 6}}>
                          <Video size={14} />
                          Video
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                  
                  <Select value={tagFilter} onValueChange={setTagFilter}>
                    <SelectTrigger style={{width: 160}}>
                      <SelectValue placeholder="Tags" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Tags</SelectItem>
                      {/* Get unique tags from resources */}
                      {Array.from(new Set(resources.flatMap(r => r.tags || []))).sort().map(tag => (
                        <SelectItem key={tag} value={tag}>{tag}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                {/* Filter Results Summary */}
                <div style={{display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.875rem', color: '#64748b'}}>
                  <span>
                    Showing {filteredResources.length} of {resources.length} resources
                  </span>
                  {(filter || typeFilter !== 'all' || tagFilter !== 'all') && (
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => {
                        setFilter('');
                        setTypeFilter('all');
                        setTagFilter('all');
                      }}
                      style={{fontSize: '0.875rem', height: 'auto', padding: '2px 8px'}}
                    >
                      Clear filters
                    </Button>
                  )}
                </div>
              </div>
              
              {/* Upload Status Display */}
              {uploadTasks.size > 0 && (
                <div style={{marginBottom: 16}}>
                  {Array.from(uploadTasks.values()).map((task) => (
                    <Card key={task.task_id} className="card" style={{marginBottom: 8}}>
                      <CardContent style={{padding: 12}}>
                        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                          <span style={{fontSize: 14}}>{task.filename}</span>
                          <span style={{
                            fontSize: 12, 
                            padding: '2px 8px', 
                            borderRadius: 4,
                            backgroundColor: task.status === 'completed' ? '#22c55e' : 
                                           task.status === 'failed' ? '#ef4444' : '#f59e0b',
                            color: 'white'
                          }}>
                            {task.status}
                          </span>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}

              {/* Upload Card */}
              <Card className="card" style={{marginBottom: 16}}>
                <CardHeader>
                  <CardTitle className="card-title">Upload Resource</CardTitle>
                </CardHeader>
                <CardContent>
                  <div>
                    <input
                      type="file"
                      accept=".pdf,.mp4,.mov,.webm"
                      onChange={handleFileUpload}
                      disabled={uploading}
                      style={{
                        width: '100%',
                        padding: '8px',
                        border: '2px dashed #ccc',
                        borderRadius: '8px',
                        textAlign: 'center',
                        cursor: uploading ? 'not-allowed' : 'pointer'
                      }}
                    />
                    <p style={{fontSize: 12, color: '#666', marginTop: 8}}>
                      Supports: PDF, MP4, QuickTime, WebM files (max 100MB)
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* Resources Grid */}
              {loading ? (
                <div style={{textAlign: 'center', padding: 32}}>
                  <p>Loading resources...</p>
                </div>
              ) : filteredResources.length === 0 ? (
                <div style={{textAlign: 'center', padding: 32}}>
                  <p>No resources found. Upload your first resource above!</p>
                </div>
              ) : (
                <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16}}>
                  {filteredResources.map((resource) => (
                    <ResourceCard key={resource.id || resource.url} resource={resource} />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function ResourceCard({ resource }) {
  const thumbnailUrl = resource.thumbnail_url ? `${BACKEND_URL}${resource.thumbnail_url}` : null;
  const knowledgeUrl = resource.knowledge_url ? `/knowledge` : null;
  
  const getKindIcon = (kind) => {
    switch(kind) {
      case 'pdf': return '📄';
      case 'video': return '🎥';
      default: return '📁';
    }
  };

  const getKindColor = (kind) => {
    switch(kind) {
      case 'pdf': return '#ef4444';
      case 'video': return '#3b82f6';
      default: return '#6b7280';
    }
  };

  return (
    <Card className="card" style={{overflow: 'hidden'}}>
      {thumbnailUrl && (
        <AspectRatio ratio={16/9}>
          <img 
            src={thumbnailUrl} 
            alt={resource.title}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover'
            }}
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
        </AspectRatio>
      )}
      <CardContent style={{padding: 16}}>
        <div style={{display: 'flex', alignItems: 'center', marginBottom: 8}}>
          <span style={{fontSize: 18, marginRight: 8}}>{getKindIcon(resource.kind)}</span>
          <span style={{
            fontSize: 12,
            padding: '2px 6px',
            backgroundColor: getKindColor(resource.kind),
            color: 'white',
            borderRadius: 4,
            textTransform: 'uppercase'
          }}>
            {resource.kind}
          </span>
        </div>
        
        <h3 style={{margin: '0 0 8px 0', fontSize: 16, fontWeight: 600}}>
          {resource.title}
        </h3>
        
        {resource.description && (
          <p style={{fontSize: 14, color: '#666', marginBottom: 8, lineHeight: 1.4}}>
            {resource.description.length > 100 
              ? `${resource.description.substring(0, 100)}...` 
              : resource.description
            }
          </p>
        )}
        
        {resource.tags && resource.tags.length > 0 && (
          <div style={{marginBottom: 8}}>
            {resource.tags.slice(0, 3).map((tag, idx) => (
              <span key={idx} style={{
                fontSize: 11,
                padding: '2px 6px',
                backgroundColor: '#f3f4f6',
                color: '#374151',
                borderRadius: 3,
                marginRight: 4,
                marginBottom: 4,
                display: 'inline-block'
              }}>
                {tag}
              </span>
            ))}
          </div>
        )}
        
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 12, color: '#666'}}>
          <span>
            {resource.uploaded_at ? new Date(resource.uploaded_at).toLocaleDateString() : 'Unknown date'}
          </span>
          
          <div style={{display: 'flex', gap: 8}}>
            {resource.url && (
              <a 
                href={`${BACKEND_URL}${resource.url}`} 
                target="_blank" 
                rel="noopener noreferrer"
                style={{color: '#3b82f6', textDecoration: 'none'}}
              >
                View
              </a>
            )}
            {knowledgeUrl && (
              <Link 
                to={knowledgeUrl}
                style={{color: '#10b981', textDecoration: 'none'}}
              >
                Knowledge
              </Link>
            )}
          </div>
        </div>
        
        {resource.knowledge_job_type && !resource.knowledge_url && (
          <div style={{marginTop: 8, fontSize: 11, color: '#f59e0b'}}>
            Processing: {resource.knowledge_job_type}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function Media() {
  const [videos] = useState([
    {
      id: 'FgKpMEowsh0',
      title: 'Hydroxychloroquine and Ivermectin Discussion', 
      description: 'Expert discussion on hydroxychloroquine and ivermectin as potential treatments for COVID-19.',
      url: 'https://www.youtube.com/watch?v=FgKpMEowsh0'
    }
    // Additional videos can be easily added to this array:
    // {
    //   id: 'VIDEO_ID_HERE',
    //   title: 'Video Title',
    //   description: 'Video description explaining the content.',
    //   url: 'https://www.youtube.com/watch?v=VIDEO_ID_HERE'
    // }
  ]);

  const getYouTubeEmbedUrl = (videoId) => {
    return `https://www.youtube.com/embed/${videoId}?rel=0&modestbranding=1`;
  };

  const extractVideoId = (url) => {
    const regex = /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/;
    const match = url.match(regex);
    return match ? match[1] : null;
  };

  return (
    <div className="App">
      <Header />
      <div className="container">
        <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px 0' }}>
          <div style={{ marginBottom: '30px', textAlign: 'center' }}>
            <h1 className="card-title" style={{ fontSize: '2rem', marginBottom: '10px' }}>Media</h1>
            <p style={{ color: '#64748b', fontSize: '1.1rem' }}>
              Curated video content on mRNA vaccines, spike protein research, and treatments
            </p>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
            {videos.map((video, index) => (
              <Card key={video.id} className="card" style={{ overflow: 'hidden' }}>
                <div style={{ position: 'relative', paddingBottom: '56.25%', height: 0 }}>
                  <iframe
                    src={getYouTubeEmbedUrl(video.id)}
                    title={video.title}
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: '100%',
                      border: 'none'
                    }}
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                </div>
                <CardContent style={{ padding: '20px' }}>
                  <h3 style={{ margin: '0 0 10px 0', fontSize: '1.25rem', fontWeight: '600' }}>
                    {video.title}
                  </h3>
                  <p style={{ color: '#64748b', margin: '0 0 15px 0', lineHeight: '1.5' }}>
                    {video.description}
                  </p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <a 
                      href={video.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        color: '#3b82f6',
                        textDecoration: 'none',
                        fontSize: '0.875rem',
                        fontWeight: '500'
                      }}
                    >
                      Watch on YouTube →
                    </a>
                  </div>
                </CardContent>
              </Card>
            ))}
            
            {/* Future videos placeholder */}
            <Card className="card" style={{ 
              border: '2px dashed #d1d5db', 
              backgroundColor: '#f9fafb',
              textAlign: 'center',
              padding: '40px 20px'
            }}>
              <CardContent>
                <h3 style={{ margin: '0 0 10px 0', color: '#6b7280' }}>More Videos Coming Soon</h3>
                <p style={{ color: '#9ca3af', margin: 0 }}>
                  We're continuously adding new educational content about mRNA vaccines and treatments.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

function Treatments() {
  return (
    <div className="App">
      <Header />
      <div className="container">
        <div className="grid">
          <Card className="card" style={{gridColumn:'span 12'}}>
            <CardHeader>
              <CardTitle className="card-title">Treatments</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Treatments page content goes here.</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Shop() {
  return (
    <div className="App">
      <Header />
      <div className="container">
        <div className="grid">
          <Card className="card" style={{gridColumn:'span 12'}}>
            <CardHeader>
              <CardTitle className="card-title">Shop</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Shop page content goes here.</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default App;