import { useMemo, useState } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { Check, ChevronLeft, ChevronRight, Clock3, Play, Plus, Users } from 'lucide-react'
import { z } from 'zod'

const apiBase = import.meta.env.VITE_API_URL ?? '/api/v1'
const weekdays = ['월', '화', '수', '목', '금', '토', '일']
type Row = Record<string, any>

function dateInSeoul() {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Seoul' }).format(new Date())
}
function shiftDate(value: string, days: number) {
  const d = new Date(`${value}T00:00:00Z`)
  d.setUTCDate(d.getUTCDate() + days)
  return d.toISOString().slice(0, 10)
}
function monday(value: string) {
  const day = new Date(`${value}T00:00:00Z`).getUTCDay()
  return shiftDate(value, day === 0 ? -6 : 1 - day)
}
function weekLabel(value: string) {
  const date = new Date(`${value}T00:00:00Z`)
  return new Intl.DateTimeFormat('ko-KR', { month: 'long', day: 'numeric', timeZone: 'Asia/Seoul' }).format(date)
}
async function request(path: string, init?: RequestInit) {
  const response = await fetch(`${apiBase}${path}`, { ...init, headers: { ...(init?.body ? { 'Content-Type': 'application/json' } : {}), ...init?.headers } })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(typeof body.detail === 'string' ? body.detail : '요청을 처리하지 못했습니다.')
  }
  return response.status === 204 ? null : response.json()
}

const scheduleSchema = z.object({
  course_id: z.string().uuid('수업을 선택해 주세요.'),
  teacher_id: z.string().uuid('선생님을 선택해 주세요.'),
  day_of_week: z.string().regex(/^[0-6]$/),
  start_time: z.string().min(1),
  end_time: z.string().min(1),
  effective_start_date: z.string().min(1),
  effective_end_date: z.string().optional(),
  room: z.string().optional(),
}).refine((v) => v.start_time < v.end_time, { path: ['end_time'], message: '종료 시간은 시작 시간보다 늦어야 합니다.' })

function SessionCard({ session, role, onChange }: { session: Row; role: string; onChange: () => void }) {
  const [expanded, setExpanded] = useState(false)
  const canManage = role === 'ACADEMY_ADMIN' || role === 'SUPER_ADMIN' || role === 'TEACHER'
  const participants = useQuery<Row[]>({ queryKey: ['session-students', session.id], queryFn: () => request(`/lesson-sessions/${session.id}/students`), enabled: expanded })
  const attendance = useMutation({ mutationFn: ({ studentId, value }: { studentId: string; value: string }) => request(`/lesson-sessions/${session.id}/students/${studentId}`, { method: 'PATCH', body: JSON.stringify({ attendance_status: value }) }), onSuccess: onChange })
  const status = useMutation({ mutationFn: (value: string) => request(`/lesson-sessions/${session.id}/status`, { method: 'PATCH', body: JSON.stringify({ status: value }) }), onSuccess: onChange })
  const time = new Intl.DateTimeFormat('ko-KR', { hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Seoul' }).format(new Date(session.scheduled_at))
  return <article className="session-card"><button className="session-summary" onClick={() => setExpanded(!expanded)}><span className={`session-dot status-${String(session.status).toLowerCase()}`}/><span className="session-time">{time}</span><span className="session-main"><strong>{session.course_name}</strong><small>{session.subject_name} · {session.teacher_name}{session.room ? ` · ${session.room}` : ''}</small></span><span className={`session-badge status-${String(session.status).toLowerCase()}`}>{({ PLANNED: '예정', IN_PROGRESS: '진행 중', COMPLETED: '완료', CANCELLED: '취소' } as Record<string,string>)[session.status]}</span><span className="participant-count"><Users size={13}/>{session.participant_count}</span></button>
    {expanded && <div className="session-details"><div className="session-detail-heading"><strong>수업 참여 학생</strong>{canManage && <span>{session.participant_count}명</span>}</div>{participants.isLoading ? <p className="panel-message">참여 학생을 불러오는 중입니다.</p> : (participants.data ?? []).length === 0 ? <p className="panel-message">참여 학생이 등록되어 있지 않습니다.</p> : participants.data?.map((person) => <div className="participant-row" key={person.id}><span>{person.student_name}</span>{canManage ? <select value={person.attendance_status} onChange={(event) => attendance.mutate({ studentId: person.student_id, value: event.target.value })}><option value="SCHEDULED">예정</option><option value="PRESENT">출석</option><option value="ABSENT">결석</option><option value="LATE">지각</option><option value="EXCUSED">사유 결석</option></select> : <span>{person.attendance_status}</span>}</div>)}{canManage && session.status === 'PLANNED' && <div className="session-controls"><button onClick={() => status.mutate('IN_PROGRESS')}><Play size={12}/> 수업 시작</button><button onClick={() => status.mutate('COMPLETED')}><Check size={13}/> 완료 처리</button></div>}{canManage && session.status === 'IN_PROGRESS' && <div className="session-controls"><button onClick={() => status.mutate('COMPLETED')}><Check size={13}/> 완료 처리</button></div>}</div>}
  </article>
}

export default function SchedulePage({ role }: { role: string }) {
  const queryClient = useQueryClient()
  const admin = role === 'ACADEMY_ADMIN' || role === 'SUPER_ADMIN'
  const superAdmin = role === 'SUPER_ADMIN'
  const [selectedDate, setSelectedDate] = useState(monday(dateInSeoul()))
  const [academyId, setAcademyId] = useState('')
  const [editing, setEditing] = useState<Row | null>(null)
  const [notice, setNotice] = useState('')
  const startDate = monday(selectedDate)
  const endDate = shiftDate(startDate, 6)
  const queryFilter = academyId ? `&academy_id=${academyId}` : ''
  const form = useForm<Record<string, any>>({ resolver: zodResolver(scheduleSchema as never), defaultValues: { day_of_week: '0', start_time: '15:00', end_time: '16:00', effective_start_date: startDate } })
  const academyQuery = useQuery<Row[]>({ queryKey: ['schedule-academies'], queryFn: () => request('/academies'), enabled: superAdmin })
  const scheduleQuery = useQuery<Row[]>({ queryKey: ['schedules', startDate, endDate, academyId], queryFn: () => request(`/schedules?start_date=${startDate}&end_date=${endDate}${queryFilter}`) })
  const sessionsQuery = useQuery<Row[]>({ queryKey: ['sessions', startDate, endDate, academyId], queryFn: () => request(`/lesson-sessions?start_date=${startDate}&end_date=${endDate}${queryFilter}`) })
  const courseQuery = useQuery<Row[]>({ queryKey: ['schedule-courses', academyId], queryFn: () => request(`/courses${academyId ? `?academy_id=${academyId}` : ''}`), enabled: admin })
  const teacherQuery = useQuery<Row[]>({ queryKey: ['schedule-teachers', academyId], queryFn: () => request(`/teachers${academyId ? `?academy_id=${academyId}` : ''}`), enabled: admin })
  const scheduleMutation = useMutation({
    mutationFn: (values: Record<string, any>) => {
      const body: Record<string, any> = { ...values, day_of_week: Number(values.day_of_week) }
      delete body.academy_id
      const target = superAdmin && academyId ? `?academy_id=${academyId}` : ''
      return editing ? request(`/schedules/${editing.id}`, { method: 'PATCH', body: JSON.stringify(body) }) : request(`/schedules${target}`, { method: 'POST', body: JSON.stringify(body) })
    },
    onSuccess: () => { setNotice(editing ? '시간표를 수정했습니다.' : '시간표를 등록했습니다.'); setEditing(null); form.reset({ day_of_week: '0', start_time: '15:00', end_time: '16:00', effective_start_date: startDate }); void queryClient.invalidateQueries({ queryKey: ['schedules'] }) },
  })
  const cancelSchedule = useMutation({ mutationFn: (id: string) => request(`/schedules/${id}`, { method: 'PATCH', body: JSON.stringify({ status: 'CANCELLED' }) }), onSuccess: () => { setNotice('반복 시간표를 휴강 처리했습니다.'); void queryClient.invalidateQueries({ queryKey: ['schedules'] }) } })
  const generateSessions = useMutation({ mutationFn: () => request(`/lesson-sessions/generate${superAdmin && academyId ? `?academy_id=${academyId}` : ''}`, { method: 'POST', body: JSON.stringify({ start_date: startDate, end_date: endDate }) }), onSuccess: (result: Row) => { setNotice(`${result.created}개의 수업 회차를 만들었습니다.`); void queryClient.invalidateQueries({ queryKey: ['sessions'] }) } })
  const scheduleRows = scheduleQuery.data ?? []
  const sessions = sessionsQuery.data ?? []
  const schedulesByDay = useMemo(() => weekdays.map((_, day) => scheduleRows.filter((row) => row.day_of_week === day)), [scheduleRows])
  const sessionsByDay = useMemo(() => weekdays.map((_, day) => sessions.filter((row) => new Date(row.scheduled_at).toLocaleDateString('en-CA', { timeZone: 'Asia/Seoul' }) === shiftDate(startDate, day))), [sessions, startDate])

  function editSchedule(row: Row) {
    setEditing(row)
    setNotice('')
    form.reset({ ...row, day_of_week: String(row.day_of_week), start_time: String(row.start_time).slice(0,5), end_time: String(row.end_time).slice(0,5), effective_end_date: row.effective_end_date ?? '' })
  }

  const formFields = [
    { name: 'course_id', label: '수업', type: 'select', options: courseQuery.data?.map((row) => [row.id, row.name]) ?? [] },
    { name: 'teacher_id', label: '담당 선생님', type: 'select', options: teacherQuery.data?.map((row) => [row.id, row.name]) ?? [] },
    { name: 'day_of_week', label: '요일', type: 'select', options: weekdays.map((day, index) => [String(index), `${day}요일`]) },
    { name: 'start_time', label: '시작 시간', type: 'time' }, { name: 'end_time', label: '종료 시간', type: 'time' },
    { name: 'effective_start_date', label: '반복 시작일', type: 'date' }, { name: 'effective_end_date', label: '반복 종료일 (선택)', type: 'date' },
    { name: 'room', label: '강의실', type: 'text' },
  ]

  return <section className="schedule-page">
    <div className="management-heading"><div><p className="eyebrow">WEEKLY CALENDAR</p><h1>시간표</h1><p className="heading-subtitle">반복 시간표와 날짜별 실제 수업 회차를 따로 관리합니다.</p></div><div className="management-actions">{superAdmin && <select className="academy-filter" value={academyId} onChange={(event) => setAcademyId(event.target.value)}><option value="">전체 학원</option>{academyQuery.data?.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select>}{admin && <button className="secondary-button" onClick={() => generateSessions.mutate()} disabled={generateSessions.isPending || (superAdmin && !academyId)}>{generateSessions.isPending ? '회차 생성 중…' : '이번 주 회차 생성'}</button>}</div></div>
    <div className="week-toolbar"><button className="icon-button" aria-label="이전 주" onClick={() => setSelectedDate(shiftDate(startDate, -7))}><ChevronLeft size={16}/></button><strong>{weekLabel(startDate)} – {weekLabel(endDate)}</strong><button className="icon-button" aria-label="다음 주" onClick={() => setSelectedDate(shiftDate(startDate, 7))}><ChevronRight size={16}/></button><input type="date" value={selectedDate} onChange={(event) => event.target.value && setSelectedDate(monday(event.target.value))}/><span className="timezone-note"><Clock3 size={13}/> Asia/Seoul</span></div>
    {notice && <p className="schedule-notice" role="status">{notice}</p>}{scheduleMutation.isError && <p className="schedule-notice error-message" role="alert">{scheduleMutation.error.message}</p>}{scheduleQuery.isError && <p className="schedule-notice error-message">{scheduleQuery.error.message}</p>}
    <div className="week-grid">{weekdays.map((day, index) => <article className="week-day" key={day}><header><strong>{day}</strong><span>{weekLabel(shiftDate(startDate,index))}</span></header><div className="day-schedules">{schedulesByDay[index].map((row) => <div className="schedule-block" key={row.id}><span>{String(row.start_time).slice(0,5)}–{String(row.end_time).slice(0,5)}</span><strong>{row.course_name}</strong><small>{row.teacher_name} · {row.room ?? '강의실 미정'}</small>{admin && <div className="schedule-block-actions"><button onClick={() => editSchedule(row)}>수정</button><button onClick={() => cancelSchedule.mutate(row.id)}>휴강</button></div>}</div>)}{schedulesByDay[index].length===0 && <p className="day-empty">예정된 반복 수업 없음</p>}</div></article>)}</div>
    <section className="sessions-section"><div className="section-heading"><div><h2>이번 주 실제 수업</h2><p>출결과 수업 진행 상태는 개별 회차에 저장됩니다.</p></div></div>{sessionsQuery.isLoading ? <p className="panel-message">수업 회차를 불러오는 중입니다.</p> : sessions.length===0 ? <div className="empty-state session-empty"><span className="empty-icon">수</span><strong>생성된 수업 회차가 없습니다</strong><p>{admin ? '반복 시간표를 등록한 뒤 이번 주 회차 생성을 눌러 주세요.' : '학원 관리자가 회차를 생성하면 이곳에 표시됩니다.'}</p></div> : weekdays.map((day,index) => sessionsByDay[index].length>0 && <div className="session-day-group" key={day}><h3>{day}요일 <span>{weekLabel(shiftDate(startDate,index))}</span></h3>{sessionsByDay[index].map((session) => <SessionCard key={session.id} session={session} role={role} onChange={() => { void queryClient.invalidateQueries({ queryKey: ['sessions'] }); void queryClient.invalidateQueries({ queryKey: ['session-students', session.id] }) }}/>)}</div>)}</section>
    {admin && <section className="panel schedule-form-panel"><div className="panel-heading"><div><h2>{editing ? '반복 시간표 수정' : '반복 수업 추가'}</h2><p>선생님 시간이 겹치는 반복 일정은 저장할 수 없습니다.</p></div>{editing && <button className="icon-button" onClick={() => { setEditing(null); form.reset() }}>취소</button>}</div><form className="schedule-form" onSubmit={form.handleSubmit((values) => scheduleMutation.mutate(values))}>{formFields.map((field) => <label className="field-label" key={field.name}>{field.label}{field.type==='select' ? <select {...form.register(field.name)} defaultValue=""><option value="">선택해 주세요</option>{(field.options ?? []).map(([value,label]) => <option value={value} key={value}>{label}</option>)}</select> : <input type={field.type} {...form.register(field.name)}/>}{form.formState.errors[field.name] && <small className="field-error">{String(form.formState.errors[field.name]?.message)}</small>}</label>)}<button className="primary-button form-submit" disabled={scheduleMutation.isPending || (superAdmin && !academyId)}><Plus size={14}/>{scheduleMutation.isPending?'저장 중…':editing?'수정 저장':'시간표 등록'}</button></form></section>}
  </section>
}
