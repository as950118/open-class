import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BookOpen, CalendarDays, Check, Clock3, GraduationCap, Users } from 'lucide-react'

type Row = Record<string, any>
const apiBase = import.meta.env.VITE_API_URL ?? '/api/v1'
async function request(path: string) {
  const response = await fetch(`${apiBase}${path}`)
  if (!response.ok) throw new Error('대시보드 정보를 불러오지 못했습니다.')
  return response.json()
}
function dateLabel(value: string) { return new Intl.DateTimeFormat('ko-KR',{hour:'2-digit',minute:'2-digit',timeZone:'Asia/Seoul'}).format(new Date(value)) }
function dayLabel() { return new Intl.DateTimeFormat('ko-KR',{dateStyle:'full',timeZone:'Asia/Seoul'}).format(new Date()) }

export default function DashboardPage({ role }: { role: string }) {
  const [academyId, setAcademyId] = useState('')
  const superAdmin = role === 'SUPER_ADMIN'
  const academies = useQuery<Row[]>({ queryKey: ['dashboard-academies'], queryFn: () => request('/academies'), enabled: superAdmin })
  const data = useQuery<Row>({ queryKey: ['dashboard', academyId], queryFn: () => request(`/dashboard${academyId ? `?academy_id=${academyId}` : ''}`) })
  const result = data.data
  const todaySessions: Row[] = result?.today_sessions ?? []
  const recentLogs: Row[] = result?.recent_logs ?? []
  const cards = [
    { label: '전체 학생', value: result?.total_students ?? '—', icon: GraduationCap, note: '현재 조회 범위' },
    { label: '선생님', value: result?.total_teachers ?? '—', icon: Users, note: '현재 조회 범위' },
    { label: '오늘 예정 수업', value: result?.today_scheduled ?? '—', icon: CalendarDays, note: dayLabel() },
    { label: '오늘 완료 수업', value: result?.today_completed ?? '—', icon: Check, note: '수업 진행 현황' },
    { label: '오늘 작성 일지', value: result?.today_logs ?? '—', icon: BookOpen, note: '학생별 학습 기록' },
    { label: '미작성 일지', value: result?.today_missing_logs ?? '—', icon: Clock3, note: '완료 수업 중 일지 없음' },
  ]
  return <section className="dashboard-page">
    <div className="management-heading"><div><p className="eyebrow">ACADEMY OVERVIEW</p><h1>대시보드</h1><p className="heading-subtitle">오늘 수업과 학습 기록 현황을 확인합니다.</p></div>{superAdmin && <select className="academy-filter" value={academyId} onChange={(e) => setAcademyId(e.target.value)}><option value="">전체 학원</option>{academies.data?.map((row) => <option value={row.id} key={row.id}>{row.name}</option>)}</select>}</div>
    {data.isError && <p className="schedule-notice error-message" role="alert">{data.error.message}</p>}
    <div className="dashboard-stats">{cards.map(({label,value,icon:Icon,note},index) => <article className="stat-card" key={label}><span className={`stat-icon tint-${index}`}><Icon size={16}/></span><span className="stat-label">{label}</span><strong>{value}</strong><small>{note}</small></article>)}</div>
    <div className="dashboard-columns"><section className="panel"><div className="panel-heading"><div><h2>오늘의 수업</h2><p>{dayLabel()} · Asia/Seoul</p></div><a className="panel-link" href="/schedules">시간표 보기 →</a></div>{data.isLoading ? <p className="panel-message">불러오는 중입니다.</p> : todaySessions.length===0 ? <div className="empty-state dashboard-empty"><span className="empty-icon"><CalendarDays size={17}/></span><strong>오늘 예정된 수업이 없습니다</strong><p>시간표에서 수업 회차를 확인할 수 있습니다.</p></div> : <div className="dashboard-list">{todaySessions.map((row: Row) => <article className="dashboard-list-row" key={row.id}><span className={`session-dot status-${String(row.status).toLowerCase()}`}/><strong>{dateLabel(row.scheduled_at)}</strong><div><b>{row.course_name}</b><small>{row.subject_name} · {row.teacher_name} · {row.participant_count}명{row.room ? ` · ${row.room}` : ''}</small></div><span className={`session-badge status-${String(row.status).toLowerCase()}`}>{row.status==='COMPLETED'?'완료':row.status==='IN_PROGRESS'?'진행 중':row.status==='CANCELLED'?'취소':'예정'}</span></article>)}</div>}</section>
      <section className="panel"><div className="panel-heading"><div><h2>최근 수업 일지</h2><p>최근 저장된 학생별 학습 기록</p></div><a className="panel-link" href="/lesson-logs">전체 보기 →</a></div>{data.isLoading ? <p className="panel-message">불러오는 중입니다.</p> : recentLogs.length===0 ? <div className="empty-state dashboard-empty"><span className="empty-icon"><BookOpen size={17}/></span><strong>아직 수업 일지가 없습니다</strong><p>수업이 완료된 후 학습 기록을 작성해 주세요.</p></div> : <div className="dashboard-list">{recentLogs.map((row: Row) => <a className="recent-log-row" href="/lesson-logs" key={row.id}><span>{new Intl.DateTimeFormat('ko-KR',{month:'numeric',day:'numeric',timeZone:'Asia/Seoul'}).format(new Date(row.scheduled_at))}</span><div><b>{row.subject || row.course_name}</b><small>{row.student_name} · {row.teacher_name} · {row.course_name}</small><p>{row.lesson_content}</p></div><span>→</span></a>)}</div>}</section></div>
  </section>
}
