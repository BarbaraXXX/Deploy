const API_BASE = '/api';

let _token: string | null = localStorage.getItem('token');

export function getToken(): string | null {
  return _token;
}

export function setToken(token: string | null): void {
  _token = token;
  if (token) {
    localStorage.setItem('token', token);
  } else {
    localStorage.removeItem('token');
  }
}

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (_token) {
    headers['Authorization'] = `Bearer ${_token}`;
  }
  return headers;
}

export async function register(username: string, password: string): Promise<{ token: string; username: string }> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.detail || 'Registration failed');
  }
  return res.json();
}

export async function login(username: string, password: string): Promise<{ token: string; username: string }> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.detail || 'Login failed');
  }
  return res.json();
}

export async function fetchDomains(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/domains`);
  const data = await res.json();
  return data.presets;
}

export async function createSession(domain: string, difficulty: string): Promise<string> {
  const res = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ domain, difficulty }),
  });
  if (res.status === 401) {
    setToken(null);
    throw new Error('UNAUTHORIZED');
  }
  const data = await res.json();
  return data.session_id;
}

export function streamChat(
  sessionId: string,
  message: string,
  onToken: (text: string) => void,
  onDone: () => void,
): AbortController {
  const controller = new AbortController();
  fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ session_id: sessionId, message }),
    signal: controller.signal,
  }).then(async (res) => {
    if (res.status === 401) {
      setToken(null);
      onDone();
      return;
    }
    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const event = JSON.parse(line.slice(6));
          if (event.type === 'token') onToken(event.content);
          else if (event.type === 'done') onDone();
        }
      }
    }
  });
  return controller;
}
