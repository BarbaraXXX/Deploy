import { useState, useRef, useEffect, useCallback } from 'react';
import { fetchDomains, createSession, fetchProfiles, streamChat, getMe, logout, login, register } from './api';

type View = 'loading' | 'login' | 'setup' | 'chat';

interface Message {
  role: 'user' | 'ai';
  content: string;
  streaming?: boolean;
}

const DIFFICULTY_OPTIONS = [
  { value: 'junior', label: '初级', meta: '实习至 1 年经验', description: '侧重基础概念、常见业务实现、代码可读性与排错思路。' },
  { value: 'mid', label: '中级', meta: '1 至 3 年经验', description: '加入工程实践、模块设计、性能取舍和线上问题处理。' },
  { value: 'senior', label: '高级', meta: '3 年以上经验', description: '强调系统设计、技术决策、复杂场景拆解和跨团队协作。' },
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

const DOMAIN_DESCRIPTIONS: Record<string, string> = {
  backend: '围绕接口设计、数据库、缓存、并发、服务稳定性和系统设计展开。',
  frontend: '覆盖组件设计、状态管理、性能优化、工程化、浏览器机制和用户体验。',
  fullstack: '兼顾前后端协作、接口边界、端到端交付、数据流与工程取舍。',
  algorithm: '聚焦数据结构、复杂度分析、编码表达、边界条件和解题思路。',
  embedded: '关注 C/C++、操作系统、硬件接口、实时性、内存管理和调试能力。',
  devops: '考察 Linux、CI/CD、容器、监控告警、发布回滚和故障定位。',
  data: '涉及 SQL、数据建模、ETL、指标口径、数据质量和分析表达。',
  security: '覆盖 Web 安全、权限模型、漏洞排查、攻防思路和安全工程实践。',
};

const getDomainDescription = (domain: string) =>
  DOMAIN_DESCRIPTIONS[domain] || '将根据你输入的方向生成更贴近该岗位的技术追问。';

function LoginView({ onLogin }: { onLogin: (username: string) => void }) {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const INVITE_CODE_EMPTY_MSG = '请输入邀请码';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (isRegister && !inviteCode.trim()) {
      setError(INVITE_CODE_EMPTY_MSG);
      return;
    }
    setLoading(true);
    try {
      const result = isRegister
        ? await register(username, password, inviteCode)
        : await login(username, password);
      onLogin(result.username);
    } catch (err) {
      setError(err instanceof Error ? err.message : '操作失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="setup-view">
      <div className="auth-layout">
        <section className="auth-intro" aria-label="产品介绍">
          <div className="brand-lockup">
            <div className="logo-mark">
              <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                <rect width="36" height="36" rx="8" fill="var(--color-accent)" />
                <path d="M10 18L16 12L22 18L16 24Z" fill="white" opacity="0.9" />
                <path d="M16 18L22 12L28 18L22 24Z" fill="white" opacity="0.6" />
              </svg>
            </div>
            <span>模拟技术面试</span>
          </div>
          <div className="auth-copy">
            <p className="eyebrow">Interview Practice</p>
            <h1 className="setup-title">用更接近真实面试的节奏完成一次技术演练</h1>
            <p className="setup-subtitle">
              登录后选择方向、难度与岗位信息，系统会按你的目标岗位生成连续追问。
            </p>
          </div>
          <div className="auth-highlights">
            <div>
              <strong>8</strong>
              <span>个预设方向</span>
            </div>
            <div>
              <strong>3</strong>
              <span>档面试难度</span>
            </div>
            <div>
              <strong>JD</strong>
              <span>岗位定制追问</span>
            </div>
          </div>
        </section>

        <section className="auth-panel" aria-label={isRegister ? '注册' : '登录'}>
          <div className="panel-heading">
            <p className="eyebrow">{isRegister ? 'Create Account' : 'Welcome Back'}</p>
            <h2>{isRegister ? '创建账号' : '登录账号'}</h2>
            <p>{isRegister ? '输入邀请码后即可开启模拟面试。' : '继续上次的面试准备流程。'}</p>
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

            {isRegister && (
              <div className="login-field">
                <label className="section-label">邀请码</label>
                <input
                  type="text"
                  className="custom-input"
                  value={inviteCode}
                  onChange={(e) => setInviteCode(e.target.value)}
                  placeholder="输入邀请码"
                  required
                />
              </div>
            )}

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
        </section>
      </div>
    </div>
  );
}

function SetupView({ onStart, username, onLogout }: {
  onStart: (domain: string, difficulty: string, jobDescription: string, profileCompany: string, profilePosition: string) => void;
  username: string;
  onLogout: () => void;
}) {
  const [domains, setDomains] = useState<string[]>(DEFAULT_DOMAINS);
  const [selectedDomain, setSelectedDomain] = useState('');
  const [customDomain, setCustomDomain] = useState('');
  const [difficulty, setDifficulty] = useState('mid');
  const [jobDescription, setJobDescription] = useState('');
  const [profiles, setProfiles] = useState<{key: string; company: string; position: string; source_count: number}[]>([]);
  const [selectedProfileIdx, setSelectedProfileIdx] = useState(-1);
  const [customCompany, setCustomCompany] = useState('');
  const [customPosition, setCustomPosition] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchDomains().then(setDomains).catch(() => {});
  }, []);

  useEffect(() => {
    fetchProfiles().then(setProfiles).catch(() => {});
  }, []);

  const activeDomain = customDomain || selectedDomain;
  const activeDomainLabel = activeDomain ? (DOMAIN_LABELS[activeDomain] || activeDomain) : '待选择';
  const activeDifficulty = DIFFICULTY_OPTIONS.find((opt) => opt.value === difficulty) || DIFFICULTY_OPTIONS[1];

  const handleStart = () => {
    if (!activeDomain || !difficulty) return;
    setLoading(true);
    let profileCompany = '';
    let profilePosition = '';
    if (selectedProfileIdx === -2) {
      profileCompany = customCompany;
      profilePosition = customPosition;
    } else if (selectedProfileIdx >= 0 && profiles[selectedProfileIdx]) {
      profileCompany = profiles[selectedProfileIdx].company;
      profilePosition = profiles[selectedProfileIdx].position;
    }
    onStart(activeDomain, difficulty, jobDescription, profileCompany, profilePosition);
  };

  return (
    <div className="setup-view">
      <div className="setup-workspace">
        <header className="setup-topbar">
          <div className="brand-lockup">
            <div className="logo-mark">
              <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                <rect width="36" height="36" rx="8" fill="var(--color-accent)" />
                <path d="M10 18L16 12L22 18L16 24Z" fill="white" opacity="0.9" />
                <path d="M16 18L22 12L28 18L22 24Z" fill="white" opacity="0.6" />
              </svg>
            </div>
            <span>模拟技术面试</span>
          </div>
          <div className="user-badge">
            <span className="user-badge-name">{username}</span>
            <button className="logout-link" onClick={onLogout}>退出</button>
          </div>
        </header>

        <div className="setup-layout">
          <aside className="setup-overview">
            <p className="eyebrow">Interview Setup</p>
            <h1 className="setup-title">配置一场更贴近目标岗位的模拟面试</h1>
            <p className="setup-subtitle">
              方向决定问题范围，难度决定追问深度，JD 会让面试更贴近真实招聘要求。
            </p>
            <div className="setup-summary">
              <div>
                <span>方向</span>
                <strong>{activeDomainLabel}</strong>
              </div>
              <div>
                <span>难度</span>
                <strong>{activeDifficulty.label}</strong>
              </div>
              <div>
                <span>岗位信息</span>
                <strong>{jobDescription.trim() ? '已提供 JD' : '未提供 JD'}</strong>
              </div>
            </div>
          </aside>

          <main className="setup-panel">
            <section className="setup-section">
              <div className="section-heading">
                <label className="section-label">技术方向</label>
                <p>选择最接近目标岗位的方向，面试官会围绕对应能力模型追问。</p>
              </div>
              <div className="domain-grid">
                {domains.map((d) => (
                  <button
                    key={d}
                    className={`domain-card ${selectedDomain === d && !customDomain ? 'active' : ''}`}
                    onClick={() => { setSelectedDomain(d); setCustomDomain(''); }}
                  >
                    <span>{DOMAIN_LABELS[d] || d}</span>
                    <small>{getDomainDescription(d)}</small>
                  </button>
                ))}
              </div>
              <div className="custom-domain">
                <input
                  type="text"
                  className="custom-input"
                  placeholder="或输入自定义方向，例如：Java 后端、AI 工程、测试开发"
                  value={customDomain}
                  onChange={(e) => { setCustomDomain(e.target.value); setSelectedDomain(''); }}
                />
              </div>
            </section>

            <section className="setup-section">
              <div className="section-heading">
                <label className="section-label">面试难度</label>
                <p>按你的目标岗位和经验年限选择，难度越高越强调方案取舍和追问深度。</p>
              </div>
              <div className="difficulty-group">
                {DIFFICULTY_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    className={`difficulty-card ${difficulty === opt.value ? 'active' : ''}`}
                    onClick={() => setDifficulty(opt.value)}
                  >
                    <span>{opt.label}</span>
                    <strong>{opt.meta}</strong>
                    <small>{opt.description}</small>
                  </button>
                ))}
              </div>
            </section>

            <section className="setup-section">
              <div className="section-heading">
                <label className="section-label">岗位JD（可选）</label>
                <p>
                  JD 是 Job Description，即招聘页面里的岗位职责和任职要求。可从招聘网站、公司官网或内推说明中复制，提供后会用于调整面试侧重点。
                </p>
              </div>
              <textarea
                className="custom-input jd-textarea"
                placeholder="粘贴岗位JD，AI将根据职责、技术栈和任职要求调整问题..."
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                rows={5}
              />
            </section>

            <section className="setup-section">
              <div className="section-heading">
                <label className="section-label">面试偏好（可选）</label>
                <p>选择公司和岗位画像后，问题会更贴近对应面经风格；也可以保持默认。</p>
              </div>
              <select
                className="custom-input profile-select"
                value={selectedProfileIdx}
                onChange={(e) => { setSelectedProfileIdx(Number(e.target.value)); setCustomCompany(''); setCustomPosition(''); }}
              >
                <option value={-1}>无</option>
                {profiles.map((p, i) => (
                  <option key={p.key} value={i}>
                    {p.company} - {p.position}（{p.source_count}份面经）
                  </option>
                ))}
                <option value={-2}>手动输入...</option>
              </select>
              {selectedProfileIdx === -2 && (
                <div className="custom-profile-inputs">
                  <input
                    type="text"
                    className="custom-input"
                    placeholder="公司名称"
                    value={customCompany}
                    onChange={(e) => setCustomCompany(e.target.value)}
                  />
                  <input
                    type="text"
                    className="custom-input"
                    placeholder="岗位名称"
                    value={customPosition}
                    onChange={(e) => setCustomPosition(e.target.value)}
                  />
                </div>
              )}
            </section>

            <button
              className="start-button"
              disabled={!activeDomain || loading}
              onClick={handleStart}
            >
              {loading ? '正在准备...' : '开始面试'}
            </button>
          </main>
        </div>
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

function LoadingView() {
  return (
    <div className="setup-view">
      <div className="loading-panel">
        <div className="logo-mark">
          <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
            <rect width="36" height="36" rx="8" fill="var(--color-accent)" />
            <path d="M10 18L16 12L22 18L16 24Z" fill="white" opacity="0.9" />
            <path d="M16 18L22 12L28 18L22 24Z" fill="white" opacity="0.6" />
          </svg>
        </div>
        <div>
          <h1>正在连接面试系统</h1>
          <p>如果后端暂时不可用，将自动进入登录页。</p>
        </div>
      </div>
    </div>
  );
}

function App() {
  const [view, setView] = useState<View>('loading');
  const [sessionId, setSessionId] = useState('');
  const [domain, setDomain] = useState('');
  const [difficulty, setDifficulty] = useState('');
  const [username, setUsername] = useState('');

  useEffect(() => {
    void getMe()
      .then((me) => {
        if (me) {
          setUsername(me.username);
          setView('setup');
        } else {
          setView('login');
        }
      })
      .catch(() => {
        setView('login');
      });
  }, []);

  const handleLogin = (user: string) => {
    setUsername(user);
    setView('setup');
  };

  const handleLogout = async () => {
    await logout();
    setUsername('');
    setView('login');
  };

  const handleStart = async (d: string, diff: string, jd: string, profileCompany: string, profilePosition: string) => {
    try {
      const sid = await createSession(d, diff, jd, profileCompany, profilePosition);
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

  return (
    <>
      {view === 'loading' && <LoadingView />}
      {view === 'login' && <LoginView onLogin={handleLogin} />}
      {view === 'setup' && <SetupView onStart={handleStart} username={username} onLogout={handleLogout} />}
      {view === 'chat' && <ChatView sessionId={sessionId} domain={domain} difficulty={difficulty} onEnd={handleEnd} />}
      <footer className="site-footer">
        <a href="https://beian.miit.gov.cn" target="_blank" rel="noopener noreferrer">
          浙ICP备2026035635号
        </a>
      </footer>
    </>
  );
}

export default App;
