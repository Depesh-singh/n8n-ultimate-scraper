"use client";

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function TopicDetail({ params }) {
  const router = useRouter();
  const topicId = params.id;

  const [topic, setTopic] = useState(null);
  const [results, setResults] = useState([]);
  const [logs, setLogs] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  
  const consoleRef = useRef(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

  // Fetch Topic details & results
  const fetchTopicData = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/topics/${topicId}`);
      if (res.ok) {
        const data = await res.json();
        setTopic(data);
        setResults(data.results || []);
      } else {
        router.push('/');
      }
      setIsLoading(false);
    } catch (err) {
      console.error("Error fetching topic detail:", err);
    }
  };

  // Fetch Crawler Logs
  const fetchLogs = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/topics/${topicId}/logs`);
      if (res.ok) {
        const logsData = await res.json();
        setLogs(logsData);
      }
    } catch (err) {
      console.error("Error fetching crawler logs:", err);
    }
  };

  useEffect(() => {
    fetchTopicData();
    fetchLogs();
    
    // Poll updates for results and logs
    const resultsInterval = setInterval(fetchTopicData, 5000);
    const logsInterval = setInterval(fetchLogs, 2000); // logs poll faster for real-time terminal feel
    
    return () => {
      clearInterval(resultsInterval);
      clearInterval(logsInterval);
    };
  }, [topicId]);

  // Auto-scroll terminal console to bottom on new logs
  useEffect(() => {
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [logs]);

  const handleSyncNow = async () => {
    setIsSyncing(true);
    try {
      await fetch(`${API_BASE}/api/topics/${topicId}/sync`, { method: 'POST' });
      // Set a brief loading indicator
      setTimeout(() => {
        fetchTopicData();
        fetchLogs();
        setIsSyncing(false);
      }, 4000);
    } catch (err) {
      console.error("Error syncing topic:", err);
      setIsSyncing(false);
    }
  };

  const handleDeleteTopic = async () => {
    if (!confirm("Are you sure you want to stop this monitoring task? This will delete all collected results.")) return;
    
    try {
      const res = await fetch(`${API_BASE}/api/topics/${topicId}`, { method: 'DELETE' });
      if (res.ok) {
        router.push('/');
      }
    } catch (err) {
      console.error("Error deleting topic:", err);
    }
  };

  const handleTogglePause = async () => {
    if (!topic) return;
    const action = topic.is_active ? 'pause' : 'resume';
    try {
      const res = await fetch(`${API_BASE}/api/topics/${topicId}/${action}`, { method: 'POST' });
      if (res.ok) {
        fetchTopicData();
        fetchLogs();
      }
    } catch (err) {
      console.error(`Error toggling pause state:`, err);
    }
  };

  // Get unique categories list for filtering
  const categories = ['all', ...new Set(results.map(r => r.category).filter(Boolean))];

  // Filter results client-side
  const filteredResults = results.filter(r => {
    const matchesSearch = 
      r.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (r.summary && r.summary.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (r.source && r.source.toLowerCase().includes(searchTerm.toLowerCase()));
      
    const matchesCategory = 
      categoryFilter === 'all' || 
      r.category === categoryFilter;

    return matchesSearch && matchesCategory;
  });

  const getModeLabel = (agent_mode) => {
    switch (agent_mode) {
      case 'url_scrape': return 'Target URL Scraper';
      case 'historical': return 'Date Archive Scraper';
      default: return 'Web Search Monitor';
    }
  };

  if (isLoading || !topic) {
    return (
      <div style={{ textAlign: 'center', padding: '100px', color: 'var(--text-secondary)' }}>
        Loading research sheet...
      </div>
    );
  }

  return (
    <div>
      {/* Header back navigation */}
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Link href="/" style={{ color: 'var(--accent-primary)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '14px', fontWeight: 500 }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="19" y1="12" x2="5" y2="12" />
            <polyline points="12 19 5 12 12 5" />
          </svg>
          Back to Dashboard
        </Link>
        <span style={{ fontSize: '13px', color: 'var(--accent-success)', display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(52, 211, 153, 0.1)', padding: '6px 12px', borderRadius: '6px', fontWeight: 600 }}>
          <span className="status-dot"></span>
          Auto-synchronized with Excel: exports/Personal_Researcher_Results.xlsx
        </span>
      </div>

      {/* Main title panel */}
      <div className="glass-panel" style={{ padding: '30px', marginBottom: '32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <h2 style={{ fontFamily: 'var(--font-outfit)', fontSize: '28px', fontWeight: 700 }}>{topic.name}</h2>
            <span className={`status-dot ${topic.is_active ? '' : 'inactive'}`} style={{ background: topic.is_active ? 'var(--accent-success)' : '#6b7280' }}></span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '6px', fontStyle: 'italic' }}>
            {topic.agent_mode === 'url_scrape' ? 'Domain Target URL: ' : topic.agent_mode === 'historical' ? 'Target Date: ' : 'Query Search Phrase: '}
            <a href={topic.agent_mode === 'url_scrape' ? topic.query : '#'} target="_blank" rel="noopener noreferrer" style={{ color: 'inherit', textDecoration: topic.agent_mode === 'url_scrape' ? 'underline' : 'none' }}>
              "{topic.query}"
            </a>
          </p>
          <div style={{ display: 'flex', gap: '20px', marginTop: '16px', fontSize: '13px', color: 'var(--text-muted)' }}>
            <div>Task Type: <strong style={{ color: 'var(--text-primary)' }}>{getModeLabel(topic.agent_mode)}</strong></div>
            {topic.agent_mode !== 'historical' && (
              <div>Interval: <strong style={{ color: 'var(--text-primary)' }}>{topic.interval_minutes} minutes</strong></div>
            )}
            <div>Items Collected: <strong style={{ color: 'var(--accent-primary)' }}>{results.length}</strong></div>
            {topic.last_searched_at && (
              <div>Last Checked: <strong style={{ color: 'var(--text-primary)' }}>{new Date(topic.last_searched_at).toLocaleString()}</strong></div>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn btn-secondary" onClick={handleSyncNow} disabled={isSyncing || !topic.is_active}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ animation: isSyncing ? 'spin 1.5s linear infinite' : 'none' }}>
              <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
            </svg>
            {isSyncing ? 'Scraping...' : 'Rescan Now'}
          </button>
          
          <a href={`${API_BASE}/api/topics/${topicId}/export`} className="btn btn-success" style={{ textDecoration: 'none' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" />
            </svg>
            Export Excel (.xlsx)
          </a>

          <button 
            className="btn" 
            style={{ 
              background: topic.is_active ? 'rgba(245, 158, 11, 0.12)' : 'rgba(16, 185, 129, 0.12)', 
              color: topic.is_active ? '#fbbf24' : '#34d399',
              border: topic.is_active ? '1px solid rgba(245, 158, 11, 0.25)' : '1px solid rgba(16, 185, 129, 0.25)',
              fontFamily: 'var(--font-outfit)'
            }} 
            onClick={handleTogglePause}
          >
            {topic.is_active ? (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="6" y="4" width="4" height="16" />
                  <rect x="14" y="4" width="4" height="16" />
                </svg>
                Pause Agent
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="5 3 19 12 5 21 5 3" />
                </svg>
                Resume Agent
              </>
            )}
          </button>

          <button className="btn btn-danger" onClick={handleDeleteTopic}>
            Delete Task
          </button>
        </div>
      </div>

      {/* Main split content grid: Spreadsheet (70%) and Live Terminal (30%) */}
      <div style={{ display: 'grid', gridTemplateColumns: '70% 30%', gap: '24px' }}>
        
        {/* LEFT PANEL: Results Spreadsheet */}
        <div>
          {/* Spreadsheet Filter Bar */}
          <div style={{ display: 'flex', gap: '16px', marginBottom: '20px' }}>
            <div style={{ flex: 1, position: 'relative' }}>
              <input 
                type="text" 
                className="form-input" 
                placeholder="Search within this sheet..." 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ paddingLeft: '40px' }}
              />
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ position: 'absolute', left: '14px', top: '13px', color: 'var(--text-muted)' }}>
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </div>

            <div style={{ width: '180px' }}>
              <select 
                className="form-select"
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <option value="all">All Categories</option>
                {categories.filter(c => c !== 'all').map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Spreadsheet Table */}
          <div className="glass-panel spreadsheet-container" style={{ minHeight: '400px' }}>
            {filteredResults.length === 0 ? (
              <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                No matching results found in this sheet.
              </div>
            ) : (
              <table className="spreadsheet-table">
                <thead>
                  <tr>
                    <th style={{ width: '50px' }}>#</th>
                    <th style={{ width: '110px' }}>Category</th>
                    <th>Title / Source</th>
                    <th style={{ width: '320px' }}>AI Extracted Summary</th>
                    <th style={{ width: '110px' }}>Date</th>
                    <th style={{ width: '80px' }}>Link</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredResults.map((item, index) => (
                    <tr key={item.id}>
                      <td style={{ color: 'var(--text-muted)', fontWeight: 600 }}>{index + 1}</td>
                      <td>
                        {item.category && (
                          <span className="category-tag" style={{ background: 'rgba(192, 132, 252, 0.15)', color: '#c084fc' }}>
                            {item.category}
                          </span>
                        )}
                      </td>
                      <td>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px', fontSize: '13px' }}>{item.title}</div>
                        <span className="source-tag" style={{ background: 'rgba(129, 140, 248, 0.12)', color: '#818cf8', fontSize: '11px', padding: '2px 6px', borderRadius: '4px' }}>
                          {item.source || 'Web'}
                        </span>
                      </td>
                      <td style={{ color: 'var(--text-secondary)', lineHeight: 1.4, fontSize: '12.5px' }}>
                        {item.summary}
                      </td>
                      <td style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                        {item.published_date && item.published_date !== 'N/A' && !isNaN(new Date(item.published_date).getTime()) 
                          ? new Date(item.published_date).toLocaleDateString() 
                          : new Date(item.discovered_at).toLocaleDateString()}
                      </td>
                      <td>
                        <a 
                          href={item.url} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          style={{ 
                            color: 'var(--accent-primary)', 
                            textDecoration: 'none', 
                            fontWeight: 600,
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            fontSize: '12px'
                          }}
                        >
                          Visit
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14 21 3" />
                          </svg>
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* RIGHT PANEL: Live Crawler Console */}
        <div>
          <h3 style={{ fontFamily: 'var(--font-outfit)', fontSize: '16px', fontWeight: 700, marginBottom: '16px', textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '0.5px' }}>Live Scraper Console</h3>
          
          <div ref={consoleRef} style={{
            background: '#090d16',
            border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: '10px',
            padding: '16px',
            height: '495px',
            overflowY: 'auto',
            fontFamily: 'Consolas, monaco, monospace',
            fontSize: '12px',
            lineHeight: '1.6',
            color: '#34d399', // emerald green text
            boxShadow: 'inset 0 4px 20px rgba(0,0,0,0.8)'
          }}>
            <div style={{ color: '#6b7280', borderBottom: '1px solid rgba(255,255,255,0.04)', paddingBottom: '8px', marginBottom: '12px', display: 'flex', justifyContent: 'space-between' }}>
              <span>TERMINAL SESSION: TOPIC_{topicId}</span>
              <span className="blink" style={{ color: 'var(--accent-success)' }}>● LOGS LIVE</span>
            </div>

            {logs.length === 0 ? (
              <div style={{ color: '#4b5563', fontStyle: 'italic' }}>
                Waiting for crawling logs... Click Rescan to trigger instant crawler action logs here.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {logs.map(log => {
                  let color = '#34d399'; // default green
                  if (log.message.includes('Error') || log.message.includes('failed')) color = '#f87171'; // red
                  else if (log.message.includes('Ollama AI') || log.message.includes('extracting')) color = '#a78bfa'; // purple
                  else if (log.message.includes('Saved:') || log.message.includes('Excel')) color = '#60a5fa'; // blue
                  else if (log.message.includes('Starting') || log.message.includes('complete')) color = '#fcd34d'; // yellow

                  return (
                    <div key={log.id} style={{ color: color, wordBreak: 'break-all' }}>
                      {log.message}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

      </div>

      <style jsx global>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        
        .blink {
          animation: blink-animation 1.5s steps(5, start) infinite;
        }

        @keyframes blink-animation {
          to { visibility: hidden; }
        }
      `}</style>
    </div>
  );
}
