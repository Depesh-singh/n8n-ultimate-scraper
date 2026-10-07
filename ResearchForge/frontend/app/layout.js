import './globals.css';
import Link from 'next/link';

export const metadata = {
  title: 'Your Personal Researcher - 24/7 Research Agent',
  description: 'Automated 24/7 internet research and continuous monitoring platform powered by AI.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <div style={{ display: 'flex' }}>
          {/* Sidebar */}
          <aside className="sidebar">
            <div style={{ marginBottom: '32px' }}>
              <h1 style={{ 
                fontFamily: 'var(--font-outfit)', 
                fontSize: '22px', 
                fontWeight: 800, 
                background: 'linear-gradient(135deg, #818cf8 0%, #c084fc 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ stroke: '#818cf8' }}>
                  <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                </svg>
                Personal Researcher
              </h1>
              <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                Your 24/7 Personal Research Agent
              </p>
            </div>

            <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <Link href="/" className="nav-link">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="3" width="7" height="9" />
                  <rect x="14" y="3" width="7" height="5" />
                  <rect x="14" y="12" width="7" height="9" />
                  <rect x="3" y="16" width="7" height="5" />
                </svg>
                Dashboard
              </Link>
              <Link href="/agent" className="nav-link">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
                AI Agent Studio
              </Link>
            </nav>

            <div style={{ 
              borderTop: '1px solid var(--border-color)', 
              paddingTop: '20px', 
              fontSize: '12px', 
              color: 'var(--text-muted)',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px'
            }}>
              <div>Agent Status: <span className="status-dot"></span> <span style={{ color: 'var(--accent-success)', fontWeight: 600 }}>Monitoring</span></div>
              <div>Model: <span style={{ color: '#818cf8', fontWeight: 500 }}>Qwen 2.5</span></div>
            </div>
          </aside>

          {/* Main Content Area */}
          <main className="main-content" style={{ flex: 1 }}>
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
