import { type FormEvent, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { BookOpen, Search, Save, X } from 'lucide-react'

type Row = Record<string, any>
const apiBase = import.meta.env.VITE_API_URL ?? '/api/v1'
const blank = { lesson_session_id: '', student_id: '', subject: '', lesson_content: '', progress_content: '', understanding_level: '', homework: '', feedback: '', next_plan: '' }

async function request(path: string, init?: RequestInit) {
  const response = await fetch(`${apiBase}${path}`, { ...init, headers: { ...(init?.body ? { 'Content-Type': 'application/json' } : {}), ...init?.headers } })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(typeof body.detail === 'string' ? body.detail : '요청을 처리하지 못했습니다.')
  }
  return response.status === 204 ? null : response.json()
}
function localDate(d: Date) { return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Seoul' }).format(d) }
function monthStart() { const now = new Date(); const seoul = new Date(`${localDate(now)}T00:00:00+09:00`); seoul.setUTCDate(1); return seoul.toISOString().slice(0,10) }
function monthEnd() { const now = new Date(); const seoul = new Date(`${localDate(now)}T00:00:00+09:00`); seoul.setUTCMonth(seoul.getUTCMonth()+1,0); return seoul.toISOString().slice(0,10) }
function displayDate(value: string) { return new Intl.DateTimeFormat('ko-KR', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Seoul' }).format(new Date(value)) }

export default function LessonLogsPage({ role }: { role: string }) {
  const queryClient = useQueryClient()
  const canWrite = role === 'ACADEMY_ADMIN' || role === 'SUPER_ADMIN' || role === 'TEACHER'
  const [search, setSearch] = useState(() => new URLSearchParams(window.location.search).get('search') ?? '')
  const [studentId, setStudentId] = useState('')
  const [teacherId, setTeacherId] = useState('')
  const [courseId, setCourseId] = useState('')
  const [startDate, setStartDate] = useState(monthStart())
  const [endDate, setEndDate] = useState(monthEnd())
  const [form, setForm] = useState(blank)
  const [editing, setEditing] = useState<Row | null>(null)
  const [notice, setNotice] = useState('')
  const logs = useQuery<Row[]>({ queryKey: ['lesson-logs', search, studentId, teacherId, courseId, startDate, endDate], queryFn: () => {
    const params = new URLSearchParams({ start_date: startDate, end_date: endDate, limit: '100' })
    if (search.trim()) params.set('search', search.trim())
    if (studentId) params.set('student_id', studentId)
    if (teacherId) params.set('teacher_id', teacherId)
    if (courseId) params.set('course_id', courseId)
    return request(`/lesson-logs?${params}`)
  } })
  const sessions = useQuery<Row[]>({ queryKey: ['completed-sessions-for-log', startDate, endDate], queryFn: () => request(`/lesson-sessions?start_date=${startDate}&end_date=${endDate}&status=COMPLETED&limit=100`), enabled: canWrite })
  const students = useQuery<Row[]>({ queryKey: ['lesson-log-students'], queryFn: () => request('/students?limit=100'), enabled: canWrite })
  const teachers = useQuery<Row[]>({ queryKey: ['lesson-log-teachers'], queryFn: () => request('/teachers?limit=100'), enabled: role !== 'STUDENT' })
  const courses = useQuery<Row[]>({ queryKey: ['lesson-log-courses'], queryFn: () => request('/courses?limit=100') })
  const participants = useQuery<Row[]>({ queryKey: ['lesson-log-participants', form.lesson_session_id], queryFn: () => request(`/lesson-sessions/${form.lesson_session_id}/students`), enabled: canWrite && !!form.lesson_session_id && !editing })
  const create = useMutation({ mutationFn: (body: Row) => request('/lesson-logs', { method: 'POST', body: JSON.stringify(body) }), onSuccess: () => { setNotice('수업 일지를 저장했습니다.'); setForm(blank); void queryClient.invalidateQueries({ queryKey: ['lesson-logs'] }) } })
  const update = useMutation({ mutationFn: ({ id, body }: { id: string; body: Row }) => request(`/lesson-logs/${id}`, { method: 'PATCH', body: JSON.stringify(body) }), onSuccess: () => { setNotice('수업 일지를 수정했습니다.'); setEditing(null); void queryClient.invalidateQueries({ queryKey: ['lesson-logs'] }) } })
  const error = create.error ?? update.error ?? logs.error
  function setField(field: string, value: string) { setForm((old) => ({ ...old, [field]: value })) }
  function startEdit(row: Row) {
    setEditing(row)
    setForm({ ...blank, ...row, lesson_session_id: row.lesson_session_id, student_id: row.student_id, understanding_level: row.understanding_level ? String(row.understanding_level) : '' })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
  function submit(event: FormEvent) {
    event.preventDefault()
    setNotice('')
    const body: Row = { ...form, understanding_level: form.understanding_level ? Number(form.understanding_level) : null }
    for (const key of Object.keys(body)) if (body[key] === '') body[key] = null
    if (editing) {
      const { lesson_session_id: _session, student_id: _student, ...patch } = body
      update.mutate({ id: editing.id, body: patch })
    } else create.mutate(body)
  }
  return <section className="management-page">
    <div className="management-heading"><div><p className="eyebrow">LEARNING JOURNAL</p><h1>수업 일지</h1><p className="heading-subtitle">학생별 학습 진도와 피드백을 수업 이력으로 기록합니다.</p></div></div>
    {(notice || error) && <p className={`schedule-notice ${error ? 'error-message' : ''}`} role={error ? 'alert' : 'status'}>{error?.message ?? notice}</p>}
    {canWrite && <section className="panel log-editor-panel"><div className="panel-heading"><div><h2>{editing ? '수업 일지 수정' : '수업 일지 작성'}</h2><p>완료된 수업 회차와 참여 학생을 선택해 주세요.</p></div>{editing && <button className="icon-button" onClick={() => { setEditing(null); setForm(blank) }} aria-label="수정 취소"><X size={15}/></button>}</div><form className="log-editor" onSubmit={submit}>
      {!editing && <><label className="field-label">완료된 수업<select required value={form.lesson_session_id} onChange={(e) => { setField('lesson_session_id',e.target.value); setField('student_id','') }}><option value="">수업 회차 선택</option>{sessions.data?.map((row) => <option key={row.id} value={row.id}>{displayDate(row.scheduled_at)} · {row.course_name} · {row.teacher_name}</option>)}</select></label><label className="field-label">참여 학생<select required value={form.student_id} onChange={(e) => setField('student_id',e.target.value)} disabled={!form.lesson_session_id}><option value="">학생 선택</option>{participants.data?.map((row) => <option key={row.student_id} value={row.student_id}>{row.student_name}</option>)}</select></label></>}
      <label className="field-label">일지 제목<input maxLength={160} value={form.subject} onChange={(e) => setField('subject',e.target.value)} placeholder="예: 분수의 나눗셈"/></label><label className="field-label log-wide">수업 내용<textarea required maxLength={12000} rows={3} value={form.lesson_content} onChange={(e) => setField('lesson_content',e.target.value)}/></label><label className="field-label">학습 진도<textarea rows={2} value={form.progress_content} onChange={(e) => setField('progress_content',e.target.value)}/></label><label className="field-label">이해도<select value={form.understanding_level} onChange={(e) => setField('understanding_level',e.target.value)}><option value="">선택 안 함</option>{[1,2,3,4,5].map((n) => <option key={n} value={n}>{n} / 5</option>)}</select></label><label className="field-label">숙제 및 과제<textarea rows={2} value={form.homework} onChange={(e) => setField('homework',e.target.value)}/></label><label className="field-label">선생님 피드백<textarea rows={2} value={form.feedback} onChange={(e) => setField('feedback',e.target.value)}/></label><label className="field-label log-wide">다음 수업 계획<textarea rows={2} value={form.next_plan} onChange={(e) => setField('next_plan',e.target.value)}/></label><button className="primary-button form-submit" disabled={create.isPending || update.isPending}><Save size={14}/>{create.isPending || update.isPending ? '저장 중…' : editing ? '수정 저장' : '일지 저장'}</button>
    </form></section>}
    <section className="panel log-list-panel"><div className="panel-heading"><div><h2>학습 기록</h2><p>학생·선생님·수업·기간·내용으로 조합 검색할 수 있습니다.</p></div></div><div className="log-filters"><label className="log-search"><Search size={15}/><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="이름, 수업, 일지 내용 검색"/></label>{canWrite && <select value={studentId} onChange={(e) => setStudentId(e.target.value)}><option value="">전체 학생</option>{students.data?.map((row) => <option value={row.id} key={row.id}>{row.name}</option>)}</select>}{role !== 'STUDENT' && <select value={teacherId} onChange={(e) => setTeacherId(e.target.value)}><option value="">전체 선생님</option>{teachers.data?.map((row) => <option value={row.id} key={row.id}>{row.name}</option>)}</select>}<select value={courseId} onChange={(e) => setCourseId(e.target.value)}><option value="">전체 수업</option>{courses.data?.map((row) => <option value={row.id} key={row.id}>{row.name}</option>)}</select><label>부터 <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)}/></label><label>까지 <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)}/></label></div>
      {logs.isLoading ? <p className="panel-message">수업 일지를 불러오는 중입니다.</p> : (logs.data ?? []).length === 0 ? <div className="empty-state log-empty"><span className="empty-icon"><BookOpen size={18}/></span><strong>검색된 수업 일지가 없습니다</strong><p>기간이나 검색어를 바꾸거나 완료된 수업의 일지를 작성해 주세요.</p></div> : <div className="log-timeline">{logs.data?.map((row) => <article className="log-entry" key={row.id}><div className="log-date"><span/>{displayDate(row.scheduled_at)}</div><div className="log-entry-card"><header><div><strong>{row.student_name}</strong><span>{row.course_name} · {row.subject_name} · {row.teacher_name}</span></div>{canWrite && <button className="icon-button" onClick={() => startEdit(row)}>수정</button>}</header>{row.subject && <h3>{row.subject}</h3>}<p>{row.lesson_content}</p>{row.progress_content && <small>진도 · {row.progress_content}</small>}{row.understanding_level && <small>이해도 · {row.understanding_level} / 5</small>}{row.homework && <small>숙제 · {row.homework}</small>}{row.feedback && <small>피드백 · {row.feedback}</small>}{row.next_plan && <small>다음 계획 · {row.next_plan}</small>}</div></article>)}</div>}
    </section>
  </section>
}
