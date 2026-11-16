import { useMemo, useState } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { type Resolver, useForm } from 'react-hook-form'
import { z } from 'zod'
import { ArrowLeft, Pencil, Plus, Search } from 'lucide-react'

const apiBase = import.meta.env.VITE_API_URL ?? '/api/v1'
export type DataKind = 'teachers' | 'students' | 'subjects' | 'courses' | 'enrollments'
type Row = Record<string, string | number | null | undefined>
type Choice = { id: string; label: string }

const title: Record<DataKind, string> = { teachers: '선생님', students: '학생', subjects: '과목', courses: '수업', enrollments: '수강 등록' }
const columns: Record<DataKind, [string, string][]> = {
  teachers: [['name', '이름'], ['email', '이메일'], ['phone', '연락처'], ['employment_status', '재직 상태']],
  students: [['name', '이름'], ['phone', '연락처'], ['email', '이메일'], ['guardian_name', '보호자'], ['status', '상태']],
  subjects: [['name', '과목명'], ['description', '설명'], ['color', '색상']],
  courses: [['name', '수업명'], ['subject_name', '과목'], ['teacher_name', '담당 선생님'], ['status', '상태']],
  enrollments: [['student_name', '학생'], ['course_name', '수업'], ['start_date', '시작일'], ['end_date', '종료일'], ['status', '상태']],
}
const messages: Record<string, string> = { ACTIVE: '재직/수강 중', ON_LEAVE: '휴직', RESIGNED: '퇴직', PAUSED: '일시 중지', WITHDRAWN: '퇴원', COMPLETED: '수강 완료', CANCELLED: '취소', CLOSED: '종료' }

const createSchemas: Record<DataKind, z.ZodTypeAny> = {
  teachers: z.object({ name: z.string().min(1, '이름을 입력해 주세요.'), email: z.string().email('올바른 이메일을 입력해 주세요.'), password: z.string().min(12, '비밀번호는 12자 이상이어야 합니다.'), phone: z.string().optional() }),
  students: z.object({ name: z.string().min(1, '이름을 입력해 주세요.'), email: z.string().email('올바른 이메일을 입력해 주세요.').or(z.literal('')), password: z.string().optional().refine((v) => !v || v.length >= 12, '비밀번호는 12자 이상이어야 합니다.'), phone: z.string().optional(), birth_date: z.string().optional(), guardian_name: z.string().optional(), guardian_phone: z.string().optional(), memo: z.string().optional() }).superRefine((v, ctx) => { if (v.password && !v.email) ctx.addIssue({ code: 'custom', path: ['email'], message: '계정을 만들려면 이메일이 필요합니다.' }) }),
  subjects: z.object({ name: z.string().min(1, '과목명을 입력해 주세요.'), description: z.string().optional(), color: z.string().regex(/^#[\da-fA-F]{6}$/, '색상 코드를 확인해 주세요.') }),
  courses: z.object({ name: z.string().min(1, '수업명을 입력해 주세요.'), subject_id: z.string().uuid('과목을 선택해 주세요.'), teacher_id: z.string().uuid('선생님을 선택해 주세요.'), description: z.string().optional() }),
  enrollments: z.object({ student_id: z.string().uuid('학생을 선택해 주세요.'), course_id: z.string().uuid('수업을 선택해 주세요.'), start_date: z.string().min(1, '시작일을 선택해 주세요.'), end_date: z.string().optional() }),
}
const editSchemas: Partial<Record<DataKind, z.ZodTypeAny>> = {
  teachers: z.object({ name: z.string().min(1), phone: z.string().optional(), employment_status: z.enum(['ACTIVE', 'ON_LEAVE', 'RESIGNED']) }),
  students: z.object({ name: z.string().min(1), phone: z.string().optional(), email: z.string().email().or(z.literal('')), birth_date: z.string().optional(), guardian_name: z.string().optional(), guardian_phone: z.string().optional(), status: z.enum(['ACTIVE', 'PAUSED', 'WITHDRAWN']), memo: z.string().optional() }),
  subjects: z.object({ name: z.string().min(1), description: z.string().optional(), color: z.string().regex(/^#[\da-fA-F]{6}$/) }),
  courses: z.object({ name: z.string().min(1), subject_id: z.string().uuid(), teacher_id: z.string().uuid(), description: z.string().optional(), status: z.enum(['ACTIVE', 'PAUSED', 'CLOSED']) }),
}

async function request(path: string, init?: RequestInit) {
  const response = await fetch(`${apiBase}${path}`, { ...init, headers: { ...(init?.body ? { 'Content-Type': 'application/json' } : {}), ...init?.headers } })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const detail = typeof body.detail === 'string' ? body.detail : '요청을 처리하지 못했습니다. 입력값과 권한을 확인해 주세요.'
    throw new Error(detail)
  }
  return response.status === 204 ? null : response.json()
}

function clean(values: Record<string, unknown>) {
  return Object.fromEntries(Object.entries(values).filter(([, value]) => value !== '' && value !== undefined))
}

export default function ManagementPage({ kind, role }: { kind: DataKind; role: string }) {
  const queryClient = useQueryClient()
  const isAdmin = role === 'SUPER_ADMIN' || role === 'ACADEMY_ADMIN'
  const [editing, setEditing] = useState<Row | null>(null)
  const [search, setSearch] = useState('')
  const [notice, setNotice] = useState('')
  const schema = editing ? (editSchemas[kind] ?? createSchemas[kind]) : createSchemas[kind]
  const resolver = zodResolver(schema as never) as Resolver<Record<string, any>>
  const form = useForm<Record<string, any>>({ resolver, defaultValues: { color: '#6474E8', status: 'ACTIVE' } })
  const selectedAcademyId = form.watch('academy_id') as string | undefined
  const listQuery = useQuery<Row[]>({ queryKey: ['academy-data', kind, search], queryFn: () => request(`/${kind}${search && ['teachers', 'students', 'courses'].includes(kind) ? `?search=${encodeURIComponent(search)}` : ''}`) })
  const academyQuery = useQuery<Row[]>({ queryKey: ['academy-data', 'academies'], queryFn: () => request('/academies'), enabled: role === 'SUPER_ADMIN' && isAdmin })
  const subjectQuery = useQuery<Row[]>({ queryKey: ['academy-data', 'subjects', selectedAcademyId], queryFn: () => request(`/subjects${selectedAcademyId ? `?academy_id=${selectedAcademyId}` : ''}`), enabled: kind === 'courses' && (role !== 'SUPER_ADMIN' || Boolean(selectedAcademyId)) })
  const teacherQuery = useQuery<Row[]>({ queryKey: ['academy-data', 'teachers', selectedAcademyId], queryFn: () => request(`/teachers${selectedAcademyId ? `?academy_id=${selectedAcademyId}` : ''}`), enabled: kind === 'courses' && (role !== 'SUPER_ADMIN' || Boolean(selectedAcademyId)) })
  const courseQuery = useQuery<Row[]>({ queryKey: ['academy-data', 'courses', selectedAcademyId], queryFn: () => request(`/courses${selectedAcademyId ? `?academy_id=${selectedAcademyId}` : ''}`), enabled: kind === 'enrollments' && (role !== 'SUPER_ADMIN' || Boolean(selectedAcademyId)) })
  const studentQuery = useQuery<Row[]>({ queryKey: ['academy-data', 'students', selectedAcademyId], queryFn: () => request(`/students${selectedAcademyId ? `?academy_id=${selectedAcademyId}` : ''}`), enabled: kind === 'enrollments' && (role !== 'SUPER_ADMIN' || Boolean(selectedAcademyId)) })

  const choices = useMemo<Record<string, Choice[]>>(() => ({
    subject_id: (subjectQuery.data ?? []).map((item) => ({ id: String(item.id), label: String(item.name) })),
    academy_id: (academyQuery.data ?? []).map((item) => ({ id: String(item.id), label: String(item.name) })),
    teacher_id: (teacherQuery.data ?? []).map((item) => ({ id: String(item.id), label: `${item.name}${item.email ? ` · ${item.email}` : ''}` })),
    course_id: (courseQuery.data ?? []).map((item) => ({ id: String(item.id), label: String(item.name) })),
    student_id: (studentQuery.data ?? []).map((item) => ({ id: String(item.id), label: String(item.name) })),
  }), [subjectQuery.data, teacherQuery.data, courseQuery.data, studentQuery.data])

  const mutation = useMutation({
    mutationFn: async (values: Record<string, unknown>) => {
      if (editing) return request(`/${kind}/${editing.id}`, { method: 'PATCH', body: JSON.stringify(clean(values)) })
      const body = clean(values)
      const tenantId = typeof body.academy_id === 'string' ? body.academy_id : undefined
      delete body.academy_id
      return request(`/${kind}${tenantId ? `?academy_id=${tenantId}` : ''}`, { method: 'POST', body: JSON.stringify(body) })
    },
    onSuccess: () => {
      setNotice(editing ? '정보를 수정했습니다.' : '새 항목을 등록했습니다.')
      setEditing(null)
      form.reset({ color: '#6474E8', status: 'ACTIVE' })
      void queryClient.invalidateQueries({ queryKey: ['academy-data'] })
    },
  })

  const fields: string[][] = kind === 'teachers'
    ? editing ? [['name', '이름', 'text'], ['phone', '연락처', 'tel'], ['employment_status', '재직 상태', 'status-teacher']] : [['name', '이름', 'text'], ['email', '로그인 이메일', 'email'], ['password', '초기 비밀번호 (12자 이상)', 'password'], ['phone', '연락처', 'tel']]
    : kind === 'students'
      ? editing ? [['name', '이름', 'text'], ['phone', '연락처', 'tel'], ['email', '이메일', 'email'], ['birth_date', '생년월일', 'date'], ['guardian_name', '보호자 이름', 'text'], ['guardian_phone', '보호자 연락처', 'tel'], ['status', '상태', 'status-student'], ['memo', '메모', 'textarea']] : [['name', '이름', 'text'], ['phone', '연락처', 'tel'], ['email', '이메일 (선택)', 'email'], ['password', '로그인 계정 비밀번호 (선택, 12자 이상)', 'password'], ['birth_date', '생년월일', 'date'], ['guardian_name', '보호자 이름', 'text'], ['guardian_phone', '보호자 연락처', 'tel'], ['memo', '메모', 'textarea']]
      : kind === 'subjects' ? [['name', '과목명', 'text'], ['description', '설명', 'text'], ['color', '표시 색상', 'color']]
        : kind === 'courses' ? editing ? [['name', '수업명', 'text'], ['subject_id', '과목', 'subject_id'], ['teacher_id', '담당 선생님', 'teacher_id'], ['description', '설명', 'text'], ['status', '상태', 'status-course']] : [['name', '수업명', 'text'], ['subject_id', '과목', 'subject_id'], ['teacher_id', '담당 선생님', 'teacher_id'], ['description', '설명', 'text']]
          : [['course_id', '수업', 'course_id'], ['student_id', '학생', 'student_id'], ['start_date', '시작일', 'date'], ['end_date', '종료일 (선택)', 'date']]
  if (role === 'SUPER_ADMIN' && isAdmin && !editing) fields.unshift(['academy_id', '학원', 'academy_id'])

  function startEditing(row: Row) {
    setEditing(row)
    setNotice('')
    form.reset({ ...row, color: row.color ?? '#6474E8', status: row.status ?? 'ACTIVE', employment_status: row.employment_status ?? 'ACTIVE', birth_date: row.birth_date ?? '', end_date: row.end_date ?? '' })
  }

  const rows = listQuery.data ?? []
  return <section className="management-page">
    <div className="management-heading"><div><p className="eyebrow">ACADEMY MANAGEMENT</p><h1>{title[kind]} 관리</h1><p className="heading-subtitle">학원 계정의 권한 범위 안에서 데이터를 확인하고 관리합니다.</p></div><div className="management-actions">{kind === 'courses' && <a className="secondary-button" href="/subjects">과목 관리</a>}{kind === 'courses' && isAdmin && <a className="secondary-button" href="/enrollments">수강 등록</a>}{kind === 'enrollments' && <a className="secondary-button" href="/courses">수업 목록</a>}</div></div>
    <div className="management-layout">
      <div className="panel data-panel"><div className="panel-heading"><div><h2>{title[kind]} 목록</h2><p>{listQuery.isLoading ? '데이터를 불러오는 중입니다.' : `${rows.length}개 항목`}</p></div><label className="table-search"><Search size={14}/><input aria-label={`${title[kind]} 검색`} placeholder="이름 검색" value={search} onChange={(event) => setSearch(event.target.value)} disabled={!['teachers', 'students', 'courses'].includes(kind)}/></label></div>
        {listQuery.isError ? <p className="panel-message error-message">{listQuery.error.message}</p> : rows.length === 0 && !listQuery.isLoading ? <div className="empty-state"><span className="empty-icon">{kind === 'students' ? '학' : kind === 'teachers' ? '선' : '수'}</span><strong>아직 등록된 {title[kind]}이 없습니다</strong><p>오른쪽 등록 양식에서 첫 항목을 추가할 수 있습니다.</p></div> : <div className="table-wrap"><table><thead><tr>{columns[kind].map(([, label]) => <th key={label}>{label}</th>)}{isAdmin && kind !== 'enrollments' && <th>관리</th>}</tr></thead><tbody>{rows.map((row) => <tr key={String(row.id)}>{columns[kind].map(([field]) => <td key={field}>{field === 'color' ? <span className="color-cell"><i style={{ backgroundColor: String(row[field] ?? '#6474E8') }}/>{String(row[field] ?? '')}</span> : messages[String(row[field])] ?? String(row[field] ?? '—')}</td>)}{isAdmin && kind !== 'enrollments' && <td><button className="icon-button" aria-label={`${row.name ?? title[kind]} 수정`} onClick={() => startEditing(row)}><Pencil size={14}/></button></td>}</tr>)}</tbody></table></div>}
      </div>
      {isAdmin && <div className="panel form-panel"><div className="panel-heading"><div><h2>{editing ? `${title[kind]} 정보 수정` : `새 ${title[kind]} 등록`}</h2><p>입력값은 저장 전에 확인합니다.</p></div>{editing && <button className="icon-button" onClick={() => { setEditing(null); form.reset({ color: '#6474E8', status: 'ACTIVE' }) }} aria-label="등록 양식으로 돌아가기"><ArrowLeft size={15}/></button>}</div>
        <form className="data-form" onSubmit={form.handleSubmit((values) => { setNotice(''); mutation.mutate(values) })}>{fields.map(([name, label, type]) => <label className="field-label" key={name}>{label}{type === 'textarea' ? <textarea rows={3} {...form.register(name)}/> : type.startsWith('status-') ? <select {...form.register(name)}>{(name === 'employment_status' ? [['ACTIVE','재직'],['ON_LEAVE','휴직'],['RESIGNED','퇴직']] : name === 'status' && kind === 'students' ? [['ACTIVE','재원'],['PAUSED','일시 중지'],['WITHDRAWN','퇴원']] : [['ACTIVE','운영'],['PAUSED','중지'],['CLOSED','종료']]).map(([value, text]) => <option value={value} key={value}>{text}</option>)}</select> : choices[name] ? <select {...form.register(name)} defaultValue=""><option value="">선택해 주세요</option>{choices[name].map((choice) => <option value={choice.id} key={choice.id}>{choice.label}</option>)}</select> : <input type={type} {...form.register(name)} placeholder={type === 'color' ? undefined : `${label} 입력`} />}{form.formState.errors[name] && <small className="field-error">{String(form.formState.errors[name]?.message)}</small>}</label>)}
          {mutation.isError && <p className="form-notice error-message" role="alert">{mutation.error.message}</p>}{notice && <p className="form-notice success-message" role="status">{notice}</p>}<button className="primary-button form-submit" disabled={mutation.isPending}>{mutation.isPending ? '저장 중…' : <><Plus size={14}/>{editing ? '수정 저장' : '등록하기'}</>}</button>
        </form>
      </div>}
    </div>
  </section>
}
