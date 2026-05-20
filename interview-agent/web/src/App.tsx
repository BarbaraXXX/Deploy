import { useState, useRef, useEffect, useCallback } from 'react';
import { fetchDomains, createSession, streamChat, getToken, setToken, login, register } from './api';

type View = 'login' | 'setup' | 'chat';

interface Message {
  role: 'user' | 'ai';
  content: string;
  streaming?: boolean;
}

const DIFFICULTY_OPTIONS = [
  { value: 'junior', label: '初级' },
  { value: 'mid', label: '中级' },
  { value: 'senior', label: '高级' },
];

const DEFAULT_DOMAINS = [
  'backend', 'frontend', 'fullstack', 'algorithm',
  'embedded', 'devops', 'data', 'security',
];

const DOMAIN_LABELS: Record<string, string> = {
  backend: '后端开发',
  frontend: '前端开发',
  fullstack: '全栈开发',
  algorithm: '算法',
  embedded: '嵌入式',
  devops: '运维',
  data: '数据',
  security: '安全',
};

function LoginView({ onLogin }: { onLogin: (username: string) => void }) {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const result = isRegister
        ? await register(username, password)
        : await login(username, password);
      setToken(result.token);
      onLogin(result.username);
    } catch (err) {
      setError(err instanceof Error ? err.message : '操作失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="setup-view">
      <div className="setup-container">
        <div className="setup-header">
          <div className="logo-mark">
            <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
              <rect width="36" height="36" rx="8" fill="var(--color-accent)" />
              <path d="M10 18L16 12L22 18L16 24Z" fill="white" opacity="0.9" />
              <path d="M16 18L22 12L28 18L22 24Z" fill="white" opacity="0.6" />
            </svg>
          </div>
          <h1 className="setup-title">模拟技术面试</h1>
          <p className="setup-subtitle">
            {isRegister ? '创建账号以开始面试' : '登录你的账号'}
          </p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="login-field">
            <label className="section-label">用户名</label>
            <input
              type="text"
              className="custom-input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="输入用户名"
              minLength={2}
              required
            />
          </div>
          <div className="login-field">
            <label className="section-label">密码</label>
            <input
              type="password"
              className="custom-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={isRegister ? '至少6位' : '输入密码'}
              minLength={6}
              required
            />
          </div>

          {error && <div className="login-error">{error}</div>}

          <button className="start-button" type="submit" disabled={loading || !username || !password}>
            {loading ? '请稍候...' : isRegister ? '注册' : '登录'}
          </button>
        </form>

        <button
          className="login-toggle"
          onClick={() => { setIsRegister(!isRegister); setError(''); }}
        >
          {isRegister ? '已有账号？去登录' : '没有账号？去注册'}
        </button>
      </div>
    </div>
  );
}

function SetupView({ onStart, username, onLogout }: {
  onStart: (domain: string, difficulty: string, jobDescription: string) => void;
  username: string;
  onLogout: () => void;
}) {
  const [domains, setDomains] = useState<string[]>(DEFAULT_DOMAINS);
  const [selectedDomain, setSelectedDomain] = useState('');
  const [customDomain, setCustomDomain] = useState('');
  const [difficulty, setDifficulty] = useState('mid');
  const [jobDescription, setJobDescription] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchDomains().then(setDomains).catch(() => {});
  }, []);

  const activeDomain = customDomain || selectedDomain;

  const handleStart = () => {
    if (!activeDomain || !difficulty) return;
    setLoading(true);
    onStart(activeDomain, difficulty, jobDescription);
  };

  return (
    <div className="setup-view">
      <div className="setup-container">
        <div className="setup-header">
          <div className="logo-mark">
            <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
              <rect width="36" height="36" rx="8" fill="var(--color-accent)" />
              <path d="M10 18L16 12L22 18L16 24Z" fill="white" opacity="0.9" />
              <path d="M16 18L22 12L28 18L22 24Z" fill="white" opacity="0.6" />
            </svg>
          </div>
          <h1 className="setup-title">模拟技术面试</h1>
          <p className="setup-subtitle">选择你的技术方向与难度，开始一场模拟面试</p>
          <div className="user-badge">
            <span className="user-badge-name">{username}</span>
            <button className="logout-link" onClick={onLogout}>退出</button>
          </div>
        </div>

        <div className="setup-section">
          <label className="section-label">技术方向</label>
          <div className="domain-grid">
            {domains.map((d) => (
              <button
                key={d}
                className={`domain-chip ${selectedDomain === d && !customDomain ? 'active' : ''}`}
                onClick={() => { setSelectedDomain(d); setCustomDomain(''); }}
              >
                {DOMAIN_LABELS[d] || d}
              </button>
            ))}
          </div>
          <div className="custom-domain">
            <input
              type="text"
              className="custom-input"
              placeholder="或输入自定义方向..."
              value={customDomain}
              onChange={(e) => { setCustomDomain(e.target.value); setSelectedDomain(''); }}
            />
          </div>
        </div>

        <div className="setup-section">
          <label className="section-label">面试难度</label>
          <div className="difficulty-group">
            {DIFFICULTY_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                className={`difficulty-pill ${difficulty === opt.value ? 'active' : ''}`}
                onClick={() => setDifficulty(opt.value)}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div className="setup-section">
          <label className="section-label">岗位JD（可选）</label>
          <textarea
            className="custom-input jd-textarea"
            placeholder="粘贴岗位JD，AI将根据JD调整面试侧重点..."
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            rows={4}
          />
        </div>

        <button
          className="start-button"
          disabled={!activeDomain || loading}
          onClick={handleStart}
        >
          {loading ? '正在准备...' : '开始面试'}
        </button>
      </div>
    </div>
  );
}

function ChatView({
  sessionId,
  domain,
  difficulty,
  onEnd,
}: {
  sessionId: string;
  domain: string;
  difficulty: string;
  onEnd: () => void;
}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || isStreaming) return;

    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: text }]);

    const aiMsgIndex = messages.length + 1;
    setMessages((prev) => [...prev, { role: 'ai', content: '', streaming: true }]);
    setIsStreaming(true);

    const controller = streamChat(
      sessionId,
      text,
      (token) => {
        setMessages((prev) =>
          prev.map((m, i) =>
            i === aiMsgIndex ? { ...m, content: m.content + token } : m,
          ),
        );
      },
      () => {
        setMessages((prev) =>
          prev.map((m, i) =>
            i === aiMsgIndex ? { ...m, streaming: false } : m,
          ),
        );
        setIsStreaming(false);
      },
    );
    abortRef.current = controller;
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleEnd = () => {
    abortRef.current?.abort();
    onEnd();
  };

  const diffLabel = DIFFICULTY_OPTIONS.find((d) => d.value === difficulty)?.label || difficulty;

  return (
    <div className="chat-view">
      <header className="chat-header">
        <div className="chat-header-info">
          <div className="chat-header-dot" />
          <span className="chat-header-domain">{DOMAIN_LABELS[domain] || domain}</span>
          <span className="chat-header-sep">/</span>
          <span className="chat-header-diff">{diffLabel}</span>
        </div>
        <button className="end-button" onClick={handleEnd}>
          结束面试
        </button>
      </header>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <p>面试即将开始，请先自我介绍吧</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`message-row ${msg.role === 'user' ? 'user' : 'ai'}`}>
            {msg.role === 'ai' && (
              <div className="ai-avatar">
                <svg width="20" height="20" viewBox="0 0 36 36" fill="none">
                  <rect width="36" height="36" rx="8" fill="var(--color-accent)" />
                  <path d="M10 18L16 12L22 18L16 24Z" fill="white" opacity="0.9" />
                  <path d="M16 18L22 12L28 18L22 24Z" fill="white" opacity="0.6" />
                </svg>
              </div>
            )}
            <div className={`message-bubble ${msg.role}`}>
              {msg.content}
              {msg.streaming && <span className="cursor-blink" />}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-bar">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入你的回答..."
          rows={1}
          disabled={isStreaming}
        />
        <button
          className="send-button"
          onClick={handleSend}
          disabled={!input.trim() || isStreaming}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  );
}

function App() {
  const [view, setView] = useState<View>('login');
  const [sessionId, setSessionId] = useState('');
  const [domain, setDomain] = useState('');
  const [difficulty, setDifficulty] = useState('');
  const [username, setUsername] = useState('');

  useEffect(() => {
    if (getToken()) {
      setView('setup');
    }
  }, []);

  const handleLogin = (user: string) => {
    setUsername(user);
    setView('setup');
  };

  const handleLogout = () => {
    setToken(null);
    setUsername('');
    setView('login');
  };

  const handleStart = async (d: string, diff: string, jd: string) => {
    try {
      const sid = await createSession(d, diff, jd);
      setSessionId(sid);
      setDomain(d);
      setDifficulty(diff);
      setView('chat');
    } catch (err) {
      if (err instanceof Error && err.message === 'UNAUTHORIZED') {
        handleLogout();
      } else {
        alert('创建会话失败，请检查后端服务是否启动');
      }
    }
  };

  const handleEnd = () => {
    setView('setup');
    setSessionId('');
  };

  if (view === 'login') {
    return <LoginView onLogin={handleLogin} />;
  }

  if (view === 'setup') {
    return <SetupView onStart={handleStart} username={username} onLogout={handleLogout} />;
  }

  return <ChatView sessionId={sessionId} domain={domain} difficulty={difficulty} onEnd={handleEnd} />;
}

export default App;
