'use client';

import { useState, useEffect, useRef } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function AgentStudio() {
  const [status, setStatus] = useState({
    state: 'idle',
    current_goal: '',
    chat_history: [],
    live_logs: [],
    challenges_count: 0,
    challenges: [],
    credential_prompt: null,
    pdf_available: false
  });

  const [inputMessage, setInputMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [credMode, setCredMode] = useState('login'); // 'login', 'otp', or 'token'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [token, setToken] = useState('');
  const [searchFilter, setSearchFilter] = useState('');
  const [selectedDomain, setSelectedDomain] = useState('ALL');
  const [expandedId, setExpandedId] = useState(null);

  const chatEndRef = useRef(null);
  const terminalEndRef = useRef(null);

  // Poll agent status every 1.5 seconds for real-time live activity
  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/agent/status`);
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
        if (data.state === 'waiting_for_otp') {
          setCredMode('otp');
        }
      }
    } catch (e) {
      console.error('Error polling agent status:', e);
    }
  };

  const prevChatCount = useRef(0);
  const prevLogsCount = useRef(0);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const currentLen = status.chat_history?.length || 0;
    if (currentLen > prevChatCount.current) {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      prevChatCount.current = currentLen;
    }
  }, [status.chat_history?.length]);

  useEffect(() => {
    const currentLen = status.live_logs?.length || 0;
    if (currentLen > prevLogsCount.current) {
      terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      prevLogsCount.current = currentLen;
    }
  }, [status.live_logs?.length]);

  const handleSendMessage = async (e) => {
    e?.preventDefault();
    if (!inputMessage.trim() || isSending) return;

    const msg = inputMessage;
    setInputMessage('');
    setIsSending(true);

    try {
      const res = await fetch(`${API_BASE}/api/agent/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg })
      });
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch (err) {
      console.error('Chat error:', err);
    } finally {
      setIsSending(false);
      fetchStatus();
    }
  };

  const handleSendCredentials = async (e) => {
    e?.preventDefault();
    setIsSending(true);

    let payload = {};
    if (credMode === 'login') {
      payload = { email: email.trim(), password: password.trim() };
    } else if (credMode === 'otp') {
      payload = { email: email.trim(), otp: otpCode.trim() };
    } else {
      payload = { token: token.trim() };
    }

    try {
      const res = await fetch(`${API_BASE}/api/agent/credentials`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
        if (credMode === 'otp') setOtpCode('');
      }
    } catch (err) {
      console.error('Credentials submit error:', err);
    } finally {
      setIsSending(false);
      fetchStatus();
    }
  };

  const handleReset = async () => {
    if (!confirm('Reset current agent mission and clear active chat?')) return;
    try {
      const res = await fetch(`${API_BASE}/api/agent/reset`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch (err) {
      console.error('Reset error:', err);
    }
  };

  // Distinct domains
  const domainsList = ['ALL', ...Array.from(new Set((status.challenges || []).map(c => c.domain || c.category || 'General').filter(Boolean)))];

  const filteredChallenges = (status.challenges || []).filter(c => {
    const q = searchFilter.toLowerCase();
    const title = (c.title || c.challengeTitle || '').toLowerCase();
    const domain = (c.domain || c.category || '').toLowerCase();
    const bg = (c.background || '').toLowerCase();
    const ch = (c.challenge || c.description || '').toLowerCase();
    const id = (c._id || c.challengeId || c.id || '').toLowerCase();

    const matchesQuery = !q || title.includes(q) || domain.includes(q) || bg.includes(q) || ch.includes(q) || id.includes(q);
    const matchesDomain = selectedDomain === 'ALL' || (c.domain || c.category || 'General').toLowerCase() === selectedDomain.toLowerCase();

    return matchesQuery && matchesDomain;
  });

  return (
    <div style={{ maxWidth: '1480px', margin: '0 auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Top Header Bar */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        background: 'var(--card-bg)',
        padding: '18px 24px',
        borderRadius: '16px',
        border: '1px solid var(--border-color)',
        boxShadow: '0 8px 30px rgba(0,0,0,0.12)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ 
            width: '46px', 
            height: '46px', 
            borderRadius: '12px', 
            background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 15px rgba(99,102,241,0.4)'
          }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2a10 10 0 0 1 10 10c0 5.523-4.477 10-10 10S2 17.523 2 12A10 10 0 0 1 12 2z" />
              <path d="M12 6v6l4 2" />
            </svg>
          </div>
          <div>
            <h1 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-main)', margin: 0, display: 'flex', alignItems: 'center', gap: '10px' }}>
              Techgium Problem Statements AI Agent
              <span style={{ 
                fontSize: '11px', 
                fontWeight: 600, 
                textTransform: 'uppercase',
                padding: '3px 10px', 
                borderRadius: '20px',
                background: status.state === 'working' ? 'rgba(234, 179, 8, 0.2)' : status.state === 'waiting_for_otp' ? 'rgba(249, 115, 22, 0.2)' : status.state === 'waiting_for_credentials' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(34, 197, 94, 0.2)',
                color: status.state === 'working' ? '#eab308' : status.state === 'waiting_for_otp' ? '#f97316' : status.state === 'waiting_for_credentials' ? '#ef4444' : '#22c55e',
                border: `1px solid ${status.state === 'working' ? '#eab308' : status.state === 'waiting_for_otp' ? '#f97316' : status.state === 'waiting_for_credentials' ? '#ef4444' : '#22c55e'}`
              }}>
                {status.state === 'working' ? '⚡ Extracting' : status.state === 'waiting_for_otp' ? '📩 Waiting for OTP' : status.state === 'waiting_for_credentials' ? '🔒 Auth Required' : '🟢 Ready'}
              </span>
            </h1>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
              Automated extraction of all official Techgium challenges across AI, Manufacturing, MedTech, Energy, Mobility & Robotics into a single unified PDF compendium.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {status.pdf_available && (
            <a 
              href={`${API_BASE}/api/agent/export-pdf`}
              download="Techgium_Problem_Statements_All.pdf"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                color: '#fff',
                padding: '10px 18px',
                borderRadius: '10px',
                fontSize: '13px',
                fontWeight: 600,
                textDecoration: 'none',
                boxShadow: '0 4px 14px rgba(16,185,129,0.3)',
                transition: 'all 0.2s'
              }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
              Download PDF ({status.challenges_count} Challenges)
            </a>
          )}

          <button 
            onClick={handleReset}
            style={{
              padding: '10px 16px',
              borderRadius: '10px',
              background: 'transparent',
              border: '1px solid var(--border-color)',
              color: 'var(--text-muted)',
              fontSize: '13px',
              cursor: 'pointer',
              fontWeight: 500
            }}
          >
            Reset Session
          </button>
        </div>
      </div>

      {/* Main Workspace Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.05fr 1fr', gap: '20px', minHeight: '720px' }}>
        
        {/* LEFT COLUMN: Interactive Chat & Input Center */}
        <div style={{ 
          background: 'var(--card-bg)', 
          borderRadius: '16px', 
          border: '1px solid var(--border-color)',
          display: 'flex',
          flexDirection: 'column',
          height: '780px',
          overflow: 'hidden',
          boxShadow: '0 8px 30px rgba(0,0,0,0.1)'
        }}>
          {/* Chat Header */}
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#818cf8" strokeWidth="2.2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
              Agent Dialogue & Feedback
            </span>
            <span style={{ fontSize: '11px', color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#10b981' }}></span>
              Connected to Techgium API
            </span>
          </div>

          {/* Chat Message Stream */}
          <div style={{ flex: 1, padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {status.chat_history.map((msg, idx) => (
              <div 
                key={idx} 
                style={{ 
                  alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '85%',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px'
                }}
              >
                <div style={{ 
                  fontSize: '11px', 
                  color: 'var(--text-muted)', 
                  alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  display: 'flex',
                  gap: '6px'
                }}>
                  <span>{msg.role === 'user' ? 'You' : 'Autonomous Agent'}</span>
                  <span>&bull;</span>
                  <span>{msg.timestamp}</span>
                </div>
                <div style={{
                  padding: '12px 16px',
                  borderRadius: msg.role === 'user' ? '14px 14px 2px 14px' : '14px 14px 14px 2px',
                  background: msg.role === 'user' ? 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)' : 'rgba(255,255,255,0.05)',
                  color: '#fff',
                  fontSize: '13.5px',
                  lineHeight: '1.5',
                  border: msg.role === 'user' ? 'none' : '1px solid var(--border-color)',
                  whiteSpace: 'pre-wrap',
                  boxShadow: msg.role === 'user' ? '0 4px 15px rgba(79,70,229,0.3)' : 'none'
                }}>
                  {msg.content}
                </div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>

          {/* Interactive Credential & OTP Card */}
          {(status.credential_prompt || status.state === 'waiting_for_otp') && (
            <div style={{ 
              margin: '0 16px 14px 16px', 
              background: 'rgba(249, 115, 22, 0.08)', 
              border: '1px solid rgba(249, 115, 22, 0.3)',
              borderRadius: '12px',
              padding: '16px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f97316" strokeWidth="2.2">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                  </svg>
                  <span style={{ fontSize: '13px', fontWeight: 700, color: '#fb923c' }}>
                    {status.state === 'waiting_for_otp' ? 'Enter 6-Digit Email OTP' : 'Techgium Authentication'}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '6px' }}>
                  <button 
                    onClick={() => setCredMode('otp')} 
                    style={{ 
                      fontSize: '11px', 
                      padding: '4px 8px', 
                      borderRadius: '6px', 
                      border: 'none',
                      background: credMode === 'otp' ? '#f97316' : 'rgba(255,255,255,0.1)',
                      color: '#fff',
                      cursor: 'pointer'
                    }}
                  >
                    Verify OTP
                  </button>
                  <button 
                    onClick={() => setCredMode('login')} 
                    style={{ 
                      fontSize: '11px', 
                      padding: '4px 8px', 
                      borderRadius: '6px', 
                      border: 'none',
                      background: credMode === 'login' ? '#f97316' : 'rgba(255,255,255,0.1)',
                      color: '#fff',
                      cursor: 'pointer'
                    }}
                  >
                    Login
                  </button>
                  <button 
                    onClick={() => setCredMode('token')} 
                    style={{ 
                      fontSize: '11px', 
                      padding: '4px 8px', 
                      borderRadius: '6px', 
                      border: 'none',
                      background: credMode === 'token' ? '#f97316' : 'rgba(255,255,255,0.1)',
                      color: '#fff',
                      cursor: 'pointer'
                    }}
                  >
                    Token
                  </button>
                </div>
              </div>

              <form onSubmit={handleSendCredentials} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {credMode === 'otp' ? (
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <input 
                      type="text" 
                      placeholder="Enter 6-digit OTP from email" 
                      value={otpCode}
                      onChange={(e) => setOtpCode(e.target.value)}
                      maxLength={6}
                      required
                      style={{ 
                        flex: 1,
                        padding: '10px 14px', 
                        borderRadius: '8px', 
                        background: 'rgba(0,0,0,0.4)', 
                        border: '1px solid rgba(249, 115, 22, 0.4)',
                        color: '#fff',
                        fontSize: '14px',
                        letterSpacing: '3px',
                        fontWeight: 700,
                        textAlign: 'center'
                      }}
                    />
                    <button 
                      type="submit" 
                      disabled={isSending || otpCode.length < 4}
                      style={{
                        padding: '10px 18px',
                        borderRadius: '8px',
                        background: '#f97316',
                        color: '#fff',
                        border: 'none',
                        fontWeight: 700,
                        fontSize: '12px',
                        cursor: 'pointer'
                      }}
                    >
                      {isSending ? 'Verifying...' : 'Verify OTP'}
                    </button>
                  </div>
                ) : credMode === 'login' ? (
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                    <input 
                      type="email" 
                      placeholder="Techgium Email" 
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      style={{ 
                        padding: '9px 12px', 
                        borderRadius: '8px', 
                        background: 'rgba(0,0,0,0.3)', 
                        border: '1px solid rgba(255,255,255,0.15)',
                        color: '#fff',
                        fontSize: '12px'
                      }}
                    />
                    <input 
                      type="password" 
                      placeholder="Password" 
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      style={{ 
                        padding: '9px 12px', 
                        borderRadius: '8px', 
                        background: 'rgba(0,0,0,0.3)', 
                        border: '1px solid rgba(255,255,255,0.15)',
                        color: '#fff',
                        fontSize: '12px'
                      }}
                    />
                  </div>
                ) : (
                  <input 
                    type="text" 
                    placeholder="Paste Bearer JWT token from browser" 
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    required
                    style={{ 
                      padding: '9px 12px', 
                      borderRadius: '8px', 
                      background: 'rgba(0,0,0,0.3)', 
                      border: '1px solid rgba(255,255,255,0.15)',
                      color: '#fff',
                      fontSize: '12px'
                    }}
                  />
                )}

                {credMode !== 'otp' && (
                  <button 
                    type="submit" 
                    disabled={isSending}
                    style={{
                      padding: '9px 14px',
                      borderRadius: '8px',
                      background: '#f97316',
                      color: '#fff',
                      border: 'none',
                      fontWeight: 600,
                      fontSize: '12px',
                      cursor: 'pointer'
                    }}
                  >
                    {isSending ? 'Authenticating...' : 'Authorize & Extract'}
                  </button>
                )}
              </form>
            </div>
          )}

          {/* Quick Guidance Chips */}
          <div style={{ padding: '0 16px 8px 16px', display: 'flex', gap: '8px', overflowX: 'auto' }}>
            <button 
              onClick={() => setInputMessage('Extract all official problem statements and update PDF')}
              style={{ padding: '6px 10px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981', color: '#34d399', fontSize: '11px', cursor: 'pointer', whiteSpace: 'nowrap', fontWeight: 600 }}
            >
              ⚡ Extract All 60 Statements
            </button>
            <button 
              onClick={() => setInputMessage('Filter only AI problem statements')}
              style={{ padding: '6px 10px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', color: '#a5b4fc', fontSize: '11px', cursor: 'pointer', whiteSpace: 'nowrap' }}
            >
              🤖 Filter: AI Only
            </button>
            <button 
              onClick={() => setInputMessage('Filter only Manufacturing problem statements')}
              style={{ padding: '6px 10px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', color: '#a5b4fc', fontSize: '11px', cursor: 'pointer', whiteSpace: 'nowrap' }}
            >
              🏭 Filter: Manufacturing Only
            </button>
            <button 
              onClick={() => setInputMessage('Show all tracks without filtering')}
              style={{ padding: '6px 10px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', color: '#cbd5e1', fontSize: '11px', cursor: 'pointer', whiteSpace: 'nowrap' }}
            >
              🔄 Reset Filters
            </button>
          </div>

          {/* Chat Input Box */}
          <form 
            onSubmit={handleSendMessage}
            style={{ 
              padding: '14px 16px', 
              borderTop: '1px solid var(--border-color)', 
              background: 'rgba(0,0,0,0.2)',
              display: 'flex',
              gap: '10px',
              alignItems: 'center'
            }}
          >
            <input 
              type="text"
              placeholder="Give instructions (e.g. 'Show only MedTech challenges' or enter OTP)..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              disabled={isSending}
              style={{
                flex: 1,
                padding: '12px 16px',
                borderRadius: '10px',
                background: 'var(--bg-main)',
                border: '1px solid var(--border-color)',
                color: '#fff',
                fontSize: '13px',
                outline: 'none'
              }}
            />
            <button 
              type="submit"
              disabled={!inputMessage.trim() || isSending}
              style={{
                padding: '12px 20px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                color: '#fff',
                border: 'none',
                fontWeight: 600,
                fontSize: '13px',
                cursor: 'pointer',
                opacity: (!inputMessage.trim() || isSending) ? 0.6 : 1,
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              {isSending ? 'Sending...' : 'Send'}
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </form>
        </div>

        {/* RIGHT COLUMN: Live Execution Stream & Problem Statements Preview */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* Live Action Monitor Terminal */}
          <div style={{
            background: '#090d16',
            borderRadius: '16px',
            border: '1px solid #1e293b',
            display: 'flex',
            flexDirection: 'column',
            height: '240px',
            overflow: 'hidden',
            boxShadow: '0 8px 25px rgba(0,0,0,0.35)'
          }}>
            <div style={{ 
              padding: '10px 16px', 
              background: '#0f172a', 
              borderBottom: '1px solid #1e293b',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ef4444' }}></span>
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#eab308' }}></span>
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#22c55e' }}></span>
                <span style={{ fontSize: '11px', fontFamily: 'monospace', color: '#94a3b8', marginLeft: '6px' }}>
                  live_agent_execution.log
                </span>
              </div>
              <span style={{ fontSize: '10px', color: '#64748b', fontFamily: 'monospace' }}>
                {status.live_logs.length} operations logged
              </span>
            </div>

            <div style={{ 
              flex: 1, 
              padding: '12px 16px', 
              overflowY: 'auto', 
              fontFamily: 'monospace', 
              fontSize: '11.5px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px'
            }}>
              {status.live_logs.length === 0 ? (
                <div style={{ color: '#475569', fontStyle: 'italic', margin: 'auto' }}>
                  Waiting for task assignment...
                </div>
              ) : (
                status.live_logs.map((log, i) => (
                  <div key={i} style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                    <span style={{ color: '#475569' }}>[{log.time}]</span>
                    <span style={{
                      color: log.level === 'action' ? '#38bdf8' : log.level === 'success' ? '#4ade80' : log.level === 'error' ? '#f87171' : log.level === 'warning' ? '#fbbf24' : '#cbd5e1'
                    }}>
                      {log.text}
                    </span>
                  </div>
                ))
              )}
              <div ref={terminalEndRef} />
            </div>
          </div>

          {/* Problem Statements Compendium List */}
          <div style={{
            background: 'var(--card-bg)',
            borderRadius: '16px',
            border: '1px solid var(--border-color)',
            display: 'flex',
            flexDirection: 'column',
            flex: 1,
            overflow: 'hidden',
            boxShadow: '0 8px 30px rgba(0,0,0,0.1)'
          }}>
            <div style={{ 
              padding: '16px 20px', 
              borderBottom: '1px solid var(--border-color)', 
              display: 'flex', 
              flexDirection: 'column',
              gap: '12px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  Official Techgium Challenges
                  <span style={{ fontSize: '12px', background: 'rgba(99,102,241,0.2)', color: '#818cf8', padding: '2px 8px', borderRadius: '12px', fontWeight: 600 }}>
                    {filteredChallenges.length} of {status.challenges_count} Items
                  </span>
                </span>

                <input 
                  type="text" 
                  placeholder="Search challenges..."
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  style={{
                    padding: '6px 12px',
                    borderRadius: '8px',
                    background: 'rgba(0,0,0,0.2)',
                    border: '1px solid var(--border-color)',
                    color: '#fff',
                    fontSize: '12px',
                    width: '180px'
                  }}
                />
              </div>

              {/* Domain Filter Pills */}
              <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', paddingBottom: '2px' }}>
                {domainsList.map(domain => (
                  <button
                    key={domain}
                    onClick={() => setSelectedDomain(domain)}
                    style={{
                      padding: '4px 10px',
                      borderRadius: '14px',
                      fontSize: '11px',
                      fontWeight: 600,
                      border: 'none',
                      cursor: 'pointer',
                      whiteSpace: 'nowrap',
                      background: selectedDomain === domain ? '#6366f1' : 'rgba(255,255,255,0.06)',
                      color: selectedDomain === domain ? '#fff' : '#94a3b8'
                    }}
                  >
                    {domain}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {filteredChallenges.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
                  <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ margin: '0 auto 12px', opacity: 0.5 }}>
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                  <p style={{ fontSize: '13px', margin: 0 }}>No problem statements match your filter.</p>
                  <p style={{ fontSize: '11px', marginTop: '4px' }}>Clear the filter or click ALL above to view all challenges.</p>
                </div>
              ) : (
                filteredChallenges.map((c, idx) => {
                  const cid = c._id ? c._id.slice(-8).toUpperCase() : (c.challengeId || c.id || `CH-${idx+1}`);
                  const title = c.title || c.challengeTitle || 'Untitled Challenge';
                  const domain = c.domain || c.category || 'General';
                  const background = c.background || '';
                  const challengeDesc = c.challenge || c.description || c.problemStatement || '';
                  const deliverables = c.deliverables || c.expectedOutput || '';
                  const isExpanded = expandedId === cid;

                  return (
                    <div 
                      key={idx}
                      style={{
                        background: 'rgba(255,255,255,0.02)',
                        border: '1px solid var(--border-color)',
                        borderRadius: '10px',
                        padding: '12px 16px',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease'
                      }}
                      onClick={() => setExpandedId(isExpanded ? null : cid)}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontSize: '11px', fontFamily: 'monospace', color: '#818cf8', fontWeight: 600 }}>
                            #{idx+1} &bull; {cid}
                          </span>
                          <span style={{ 
                            fontSize: '10px', 
                            background: 'rgba(59, 130, 246, 0.15)', 
                            color: '#60a5fa', 
                            padding: '2px 8px', 
                            borderRadius: '4px',
                            fontWeight: 600
                          }}>
                            {domain}
                          </span>
                        </div>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          {isExpanded ? '▲ Less' : '▼ Details'}
                        </span>
                      </div>

                      <div style={{ fontSize: '13.5px', fontWeight: 600, color: '#f1f5f9', lineHeight: '1.4' }}>
                        {title}
                      </div>

                      {isExpanded && (
                        <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--border-color)', fontSize: '12.5px', color: '#cbd5e1', lineHeight: '1.6', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                          {background && (
                            <div>
                              <strong style={{ color: '#38bdf8' }}>1. Background & Context:</strong>
                              <p style={{ margin: '4px 0 0 0', color: '#94a3b8' }}>{background}</p>
                            </div>
                          )}
                          {challengeDesc && (
                            <div>
                              <strong style={{ color: '#818cf8' }}>2. Challenge Statement:</strong>
                              <p style={{ margin: '4px 0 0 0', color: '#e2e8f0' }}>{challengeDesc}</p>
                            </div>
                          )}
                          {deliverables && (
                            <div>
                              <strong style={{ color: '#34d399' }}>3. Expected Deliverables:</strong>
                              <p style={{ margin: '4px 0 0 0', color: '#94a3b8', whiteSpace: 'pre-line' }}>{deliverables}</p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
