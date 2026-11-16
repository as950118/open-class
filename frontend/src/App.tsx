import { type FormEvent, useEffect, useState } from 'react'
import { BookOpen, CalendarDays, ChevronDown, GraduationCap, LayoutDashboard, Search, Settings, Users, Wifi, WifiOff } from 'lucide-react'
import { useLocation, useNavigate } from 'react-router-dom'
import ManagementPage, { type DataKind } from './features/academy-data/ManagementPage'
import SchedulePage from './features/schedules/SchedulePage'
import LessonLogsPage from './features/lesson-logs/LessonLogsPage'
import DashboardPage from './features/dashboard/DashboardPage'

const navigation = [
  { label: '대시보드', icon: LayoutDashboard, path: '/' },
  { label: '시간표', icon: CalendarDays, path: '/schedules' },
  { label: '선생님', icon: Users, path: '/teachers' },
  { label: '학생', icon: GraduationCap, path: '/students' },
  { label: '수업', icon: BookOpen, path: '/courses' },
  { label: '수업 일지', icon: BookOpen, path: '/lesson-logs' },
]
const dataPages: Record<string, DataKind> = { '/teachers': 'teachers', '/students': 'students', '/subjects': 'subjects', '/courses': 'courses', '/enrollments': 'enrollments' }
const routeTitles: Record<string, string> = { '/': '대시보드', '/schedules': '시간표', '/lesson-logs': '수업 일지', '/teachers': '선생님', '/students': '학생', '/subjects': '과목', '/courses': '수업', '/enrollments': '수강 등록' }

type Account = { id: string; academy_id: string | null; academy_name: string | null; email: string; name: string; role: 'SUPER_ADMIN' | 'ACADEMY_ADMIN' | 'TEACHER' | 'STUDENT'; is_active: boolean }
type SearchGroups = Record<string, { id: string; title: string; subtitle: string; path: string }[]>
const apiBase = import.meta.env.VITE_API_URL ?? '/api/v1'
const roleNames: Record<Account['role'], string> = { SUPER_ADMIN: '플랫폼 관리자', ACADEMY_ADMIN: '학원 관리자', TEACHER: '선생님', STUDENT: '학생' }

export default function App() {
  const location = useLocation()
  const navigate = useNavigate()
  const [apiStatus, setApiStatus] = useState<'loading' | 'connected' | 'error'>('loading')
  const [account, setAccount] = useState<Account | null>(null)
  const [sessionReady, setSessionReady] = useState(false)
  const [loginError, setLoginError] = useState('')
  const [loginPending, setLoginPending] = useState(false)
  const [globalQuery, setGlobalQuery] = useState('')
  const [globalResults, setGlobalResults] = useState<SearchGroups>({})
  const [searchOpen, setSearchOpen] = useState(false)
  const page = dataPages[location.pathname]
  const schedulePage = location.pathname === '/schedules'
  const lessonLogsPage = location.pathname === '/lesson-logs'

  useEffect(() => {
    if (globalQuery.trim().length < 2) { setGlobalResults({}); return }
    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      fetch(`${apiBase}/search?q=${encodeURIComponent(globalQuery.trim())}`, { signal: controller.signal }).then((response) => response.ok ? response.json() : {}).then(setGlobalResults).catch((error) => { if (error.name !== 'AbortError') setGlobalResults({}) })
    }, 250)
    return () => { window.clearTimeout(timer); controller.abort() }
  }, [globalQuery])

  useEffect(() => {
    fetch(`${apiBase}/health`).then((response) => {
      if (!response.ok) throw new Error('API 연결 실패')
      return response.json()
    }).then((health: { status: string; database: string }) => {
      setApiStatus(health.status === 'ok' && health.database === 'connected' ? 'connected' : 'error')
    }).catch(() => setApiStatus('error'))
    fetch(`${apiBase}/auth/me`).then((response) => response.ok ? response.json() : null)
      .then((user: Account | null) => setAccount(user)).catch(() => setAccount(null))
      .finally(() => setSessionReady(true))
  }, [])

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoginPending(true)
    setLoginError('')
    const form = new FormData(event.currentTarget)
    try {
      const response = await fetch(`${apiBase}/auth/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: form.get('email'), password: form.get('password') }),
      })
      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        throw new Error(typeof body.detail === 'string' ? body.detail : '로그인에 실패했습니다.')
      }
      const current = await fetch(`${apiBase}/auth/me`)
      if (!current.ok) throw new Error('계정 정보를 불러오지 못했습니다.')
      setAccount(await current.json())
    } catch (error) {
      setLoginError(error instanceof Error ? error.message : '로그인 중 오류가 발생했습니다.')
    } finally {
      setLoginPending(false)
    }
  }

  async function logout() {
    const response = await fetch(`${apiBase}/auth/logout`, { method: 'POST' })
    if (response.ok) setAccount(null)
  }

  if (!sessionReady) return <main className="auth-loading">open-class 연결을 확인하고 있어요…</main>
  if (!account) return <main className="auth-page"><section className="auth-card"><a className="brand auth-brand" href="#home"><span className="brand-mark"><BookOpen size={18}/></span><span className="brand-name">open<span>-</span>class</span></a><p className="eyebrow">ACADEMY WORKSPACE</p><h1>다시 만나 반가워요</h1><p className="auth-subtitle">학원 계정으로 로그인해 주세요.</p><form onSubmit={login} className="auth-form"><label htmlFor="email">이메일</label><input id="email" name="email" type="email" autoComplete="username" placeholder="name@academy.com" required/><label htmlFor="password">비밀번호</label><input id="password" name="password" type="password" autoComplete="current-password" placeholder="비밀번호를 입력해 주세요" required/><p className="auth-error" role="alert">{loginError}</p><button className="primary-button auth-submit" type="submit" disabled={loginPending}>{loginPending?'로그인 중…':'로그인'}</button></form><div className={`auth-connection ${apiStatus}`}><span className="connection-dot"/>{apiStatus==='connected'?'API 및 데이터베이스 연결됨':apiStatus==='error'?'서비스 연결을 확인해 주세요':'서비스 연결 확인 중'}</div></section><footer className="auth-footer">© 2026 open-class · Asia/Seoul</footer></main>

  return <div className="app-shell min-h-screen">
    <aside className="sidebar">
      <button className="brand brand-button" onClick={() => navigate('/')}><span className="brand-mark"><BookOpen size={18}/></span><span className="brand-name">open<span>-</span>class</span></button>
      <div className="academy-switcher"><span className="academy-avatar">{(account.academy_name ?? 'O').slice(0,1)}</span><span className="academy-copy"><strong>{account.academy_name ?? 'Open Class'}</strong><small>{roleNames[account.role]}</small></span><ChevronDown size={15}/></div>
      <p className="nav-caption">워크스페이스</p>
      <nav aria-label="주 메뉴">{navigation.map(({label,icon:Icon,path})=><button className={`nav-link${path===location.pathname?' active':''}`} aria-current={path===location.pathname?'page':undefined} disabled={!path} onClick={() => path && navigate(path)} key={label}><Icon size={17}/><span>{label}</span></button>)}</nav>
      <div className="sidebar-bottom"><button className="nav-link" disabled><Settings size={17}/><span>설정</span></button><div className="profile-card"><div className="profile-avatar">{account.name.slice(0,1)}</div><div className="profile-copy"><strong>{account.name}</strong><small>{roleNames[account.role]}</small></div><button className="logout-link" onClick={logout}>로그아웃</button></div></div>
    </aside>
    <main className="main-area">
      <header className="topbar"><div className="breadcrumb"><span>{account.academy_name ?? 'Open Class'}</span><b>/</b><strong>{routeTitles[location.pathname] ?? '대시보드'}</strong></div><div className="top-actions"><div className="global-search-wrap"><label className="global-search"><Search size={15}/><input value={globalQuery} onFocus={() => setSearchOpen(true)} onChange={(e) => { setGlobalQuery(e.target.value); setSearchOpen(true) }} onKeyDown={(e) => { if (e.key === 'Escape') setSearchOpen(false) }} placeholder="학생, 선생님, 수업 검색"/><kbd>⌘ K</kbd></label>{searchOpen && globalQuery.trim().length >= 2 && <div className="global-search-results">{Object.entries(globalResults).flatMap(([group, rows]) => rows.map((row) => ({ ...row, group }))).length === 0 ? <p>검색 결과가 없습니다.</p> : Object.entries(globalResults).flatMap(([group, rows]) => rows.map((row) => <button key={`${group}-${row.id}`} onClick={() => { navigate(row.path); setSearchOpen(false) }}><span>{row.title}</span><small>{row.subtitle}</small></button>))}</div>}</div><span className={`api-pill ${apiStatus}`}>{apiStatus==='connected'?<Wifi size={14}/>:<WifiOff size={14}/>} {apiStatus==='connected'?'API 연결됨':apiStatus==='error'?'API 연결 안 됨':'API 확인 중'}</span><button className="top-avatar" onClick={logout} aria-label="로그아웃" title="로그아웃">{account.name.slice(0,1)}</button></div></header>
      <div className="page-content">
        {page ? <ManagementPage kind={page} role={account.role}/> : schedulePage ? <SchedulePage role={account.role}/> : lessonLogsPage ? <LessonLogsPage role={account.role}/> : <DashboardPage role={account.role}/>}
      </div>
    </main>
  </div>
}
