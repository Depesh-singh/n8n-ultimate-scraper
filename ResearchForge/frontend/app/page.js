"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';

export default function Dashboard() {
  const [stats, setStats] = useState({
    total_topics: 0,
    total_results: 0,
    discoveries_today: 0,
    active_monitors: 0,
    recent_discoveries: []
  });
  
  const [topics, setTopics] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newTopic, setNewTopic] = useState({
    name: '',
    query: '',
    search_type: 'both',
    interval_minutes: 15,
    agent_mode: 'search'
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

  // Fetch Dashboard Stats & Topics
  const fetchData = async () => {
    try {
      const statsRes = await fetch(`${API_BASE}/api/analytics`);
      const statsData = await statsRes.json();
      setStats(statsData);

      const topicsRes = await fetch(`${API_BASE}/api/topics`);
      const topicsData = await topicsRes.json();
      setTopics(topicsData);
      
      setIsLoading(false);
    } catch (err) {
      console.error("Error fetching dashboard data:", err);
    }
  };

  useEffect(() => {
    fetchData();
    // Poll updates every 10 seconds
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleCreateTopic = async (e) => {
    e.preventDefault();
    if (!newTopic.name || !newTopic.query) return;
    
    setIsSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/topics`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTopic)
      });
      
      if (res.ok) {
        setIsModalOpen(false);
        setNewTopic({ name: '', query: '', search_type: 'both', interval_minutes: 15, agent_mode: 'search' });
        fetchData();
      }
    } catch (err) {
      console.error("Error creating topic:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getModeLabel = (agent_mode) => {
    switch (agent_mode) {
      case 'url_scrape': return 'URL Scraper';
      case 'historical': return 'Date Archive';
      default: return 'Web Search';
    }
  };

  const getModeColor = (agent_mode) => {
    switch (agent_mode) {
      case 'url_scrape': return '#38bdf8'; // sky blue
      case 'historical': return '#fb923c'; // orange
      default: return '#818cf8'; // indigo
    }
  };

  return (
    <div>
      {/* Upper header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h2 style={{ fontFamily: 'var(--font-outfit)', fontSize: '28px', fontWeight: 700 }}>Research Console</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '4px' }}>Continuous 24/7 web monitoring, target URL scraping, and historical date extraction engine</p>
        </div>
        <button className="btn btn-primary" onClick={() => setIsModalOpen(true)}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Add Research Task
        </button>
      </div>

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px', marginBottom: '40px' }}>
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '0.5px' }}>Active Monitors</div>
          <div style={{ fontSize: '36px', fontWeight: 800, fontFamily: 'var(--font-outfit)', marginTop: '8px', color: '#818cf8' }}>
            {isLoading ? '...' : stats.active_monitors}
          </div>
        </div>
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '0.5px' }}>Total Discoveries</div>
          <div style={{ fontSize: '36px', fontWeight: 800, fontFamily: 'var(--font-outfit)', marginTop: '8px', color: '#c084fc' }}>
            {isLoading ? '...' : stats.total_results}
          </div>
        </div>
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '0.5px' }}>Found Today</div>
          <div style={{ fontSize: '36px', fontWeight: 800, fontFamily: 'var(--font-outfit)', marginTop: '8px', color: 'var(--accent-success)' }}>
            {isLoading ? '...' : stats.discoveries_today}
          </div>
        </div>
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '0.5px' }}>Workspace Sync</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '16px' }}>
            <span className="status-dot"></span>
            <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>Excel Live Connected</span>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '30px' }}>
        {/* Active Research Tasks grid */}
        <div>
          <h3 style={{ fontFamily: 'var(--font-outfit)', fontSize: '20px', fontWeight: 700, marginBottom: '20px' }}>Active Researchers</h3>
          
          {isLoading ? (
            <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
              Loading research tasks...
            </div>
          ) : topics.length === 0 ? (
            <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
              No active research tasks. Add your first topic above!
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '20px' }}>
              {topics.map(topic => (
                <Link key={topic.id} href={`/topic/${topic.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                  <div className="glass-panel" style={{ padding: '24px', cursor: 'pointer', transition: 'all 0.2s ease', position: 'relative' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                      <h4 style={{ fontFamily: 'var(--font-outfit)', fontSize: '18px', fontWeight: 600, maxWidth: '80%' }}>{topic.name}</h4>
                      <span className={`status-dot ${topic.is_active ? '' : 'inactive'}`} style={{ background: topic.is_active ? 'var(--accent-success)' : '#6b7280' }}></span>
                    </div>
                    
                    <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                      {topic.agent_mode === 'url_scrape' ? 'URL: ' : 'Query: '}"{topic.query}"
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', gap: '12px', fontSize: '12px', color: 'var(--text-muted)' }}>
                        {topic.agent_mode !== 'historical' && (
                          <div>Interval: <strong>{topic.interval_minutes}m</strong></div>
                        )}
                        <div style={{ color: getModeColor(topic.agent_mode), fontWeight: 700 }}>
                          {getModeLabel(topic.agent_mode)}
                        </div>
                      </div>
                    </div>

                    <div style={{ borderTop: '1px solid var(--border-color)', marginTop: '16px', paddingTop: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                        Synced: {topic.last_searched_at ? new Date(topic.last_searched_at).toLocaleTimeString() : 'Never'}
                      </div>
                      <div style={{ background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', fontWeight: 700, fontSize: '12px', padding: '4px 10px', borderRadius: '20px' }}>
                        {topic.results_count} found
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Live Discoveries Side Panel */}
        <div>
          <h3 style={{ fontFamily: 'var(--font-outfit)', fontSize: '20px', fontWeight: 700, marginBottom: '20px' }}>Live Discoveries Feed</h3>
          <div className="glass-panel" style={{ padding: '20px', maxHeight: '520px', overflowY: 'auto' }}>
            {isLoading ? (
              <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '20px' }}>Loading feed...</div>
            ) : stats.recent_discoveries.length === 0 ? (
              <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '20px' }}>Waiting for discoveries...</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {stats.recent_discoveries.map(item => (
                  <div key={item.id} style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                      <span>{item.topic_name}</span>
                      <span>{new Date(item.discovered_at).toLocaleTimeString()}</span>
                    </div>
                    <a href={item.url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-primary)', textDecoration: 'none', fontWeight: 500, fontSize: '13px', display: 'block', lineHeight: 1.4 }}>
                      {item.title}
                    </a>
                    <div style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
                      <span className="source-tag" style={{ fontSize: '10px', padding: '2px 6px' }}>{item.source}</span>
                      {item.category && <span className="category-tag" style={{ fontSize: '10px', padding: '2px 6px' }}>{item.category}</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* New Topic Creation Modal */}
      {isModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content glass-panel">
            <h3 style={{ fontFamily: 'var(--font-outfit)', fontSize: '20px', fontWeight: 700, marginBottom: '20px' }}>New Research Task</h3>
            <form onSubmit={handleCreateTopic}>
              
              <div className="form-group" style={{ marginBottom: '16px' }}>
                <label className="form-label">Research Agent Mode</label>
                <select 
                  className="form-select"
                  value={newTopic.agent_mode}
                  onChange={(e) => {
                    const agent_mode = e.target.value;
                    setNewTopic({
                      ...newTopic,
                      agent_mode: agent_mode,
                      query: '',
                      name: ''
                    });
                  }}
                >
                  <option value="search">24/7 Web Search Monitor</option>
                  <option value="url_scrape">Target Website Scraper (URL)</option>
                  <option value="historical">Date-Wise Event Scraper</option>
                </select>
              </div>

              {newTopic.agent_mode === 'search' && (
                <>
                  <div className="form-group">
                    <label className="form-label">Research Task Name</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      placeholder="e.g. BJP News Tracker" 
                      value={newTopic.name}
                      onChange={(e) => setNewTopic({ ...newTopic, name: e.target.value })}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Search Query</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      placeholder="e.g. bjp latest news politics" 
                      value={newTopic.query}
                      onChange={(e) => setNewTopic({ ...newTopic, query: e.target.value })}
                      required
                    />
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                    <div className="form-group">
                      <label className="form-label">Search Type</label>
                      <select 
                        className="form-select"
                        value={newTopic.search_type}
                        onChange={(e) => setNewTopic({ ...newTopic, search_type: e.target.value })}
                      >
                        <option value="both">Web & News</option>
                        <option value="news">News Only</option>
                        <option value="web">Web Search Only</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label className="form-label">Scan Interval</label>
                      <select 
                        className="form-select"
                        value={newTopic.interval_minutes}
                        onChange={(e) => setNewTopic({ ...newTopic, interval_minutes: parseInt(e.target.value) })}
                      >
                        <option value={5}>Every 5 minutes</option>
                        <option value={15}>Every 15 minutes</option>
                        <option value={30}>Every 30 minutes</option>
                        <option value={60}>Every 1 hour</option>
                      </select>
                    </div>
                  </div>
                </>
              )}

              {newTopic.agent_mode === 'url_scrape' && (
                <>
                  <div className="form-group">
                    <label className="form-label">Task Name (Filter Item)</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      placeholder="e.g. AI Internships Tracker" 
                      value={newTopic.name}
                      onChange={(e) => setNewTopic({ ...newTopic, name: e.target.value })}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Target Website URL</label>
                    <input 
                      type="url" 
                      className="form-input" 
                      placeholder="e.g. https://news.ycombinator.com" 
                      value={newTopic.query}
                      onChange={(e) => setNewTopic({ ...newTopic, query: e.target.value })}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Scan Interval</label>
                    <select 
                      className="form-select"
                      value={newTopic.interval_minutes}
                      onChange={(e) => setNewTopic({ ...newTopic, interval_minutes: parseInt(e.target.value) })}
                    >
                      <option value={5}>Every 5 minutes</option>
                      <option value={15}>Every 15 minutes</option>
                      <option value={30}>Every 30 minutes</option>
                      <option value={60}>Every 1 hour</option>
                    </select>
                  </div>
                </>
              )}

              {newTopic.agent_mode === 'historical' && (
                <>
                  <div className="form-group">
                    <label className="form-label">Archive Task Name</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      placeholder="e.g. March 3rd 2026 Major Incidents" 
                      value={newTopic.name}
                      onChange={(e) => setNewTopic({ ...newTopic, name: e.target.value })}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Target Date</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      placeholder="e.g. 3 March 2026" 
                      value={newTopic.query}
                      onChange={(e) => setNewTopic({ ...newTopic, query: e.target.value })}
                      required
                    />
                  </div>
                </>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '20px' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                  {isSubmitting ? 'Launching...' : 'Launch Agent'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
