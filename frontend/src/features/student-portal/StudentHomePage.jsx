import { useQuery } from '@tanstack/react-query'
import { ArrowUpRight, BookOpen, CalendarDays, CheckSquare, Clock3, GraduationCap, UsersRound } from 'lucide-react'
import { request } from '@/lib/apiClient'
import { useAuth } from '@/features/auth/AuthContext'

const dash = (value) => value || '-'
const SEX_LABELS = { FEMALE: 'Female', MALE: 'Male' }
const TODAY_LABEL = new Intl.DateTimeFormat('en-GB', { weekday: 'long', day: 'numeric', month: 'long' }).format(new Date())

const SAMPLE_STUDENT = {
  student_id: 'S0000',
  full_name: 'Sample Student',
  khmer_name: '',
  sex: 'FEMALE',
  date_of_birth: '2014-01-01',
  nationality_1: 'Cambodian',
  nationality_2: '',
  grade: 'Year 7',
  enrollment_status: 'Existing',
  guardians: [{ full_name: 'Sample Parent', relationship: 'Mother' }],
}

export default function StudentHomePage() {
  const { token, actualRole } = useAuth()
  const isRealStudent = actualRole === 'STUDENT'
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['my-student'],
    queryFn: () => request('/me/student/', {}, token),
    enabled: Boolean(token) && isRealStudent,
  })
  const student = isRealStudent ? data : SAMPLE_STUDENT

  if (isRealStudent && isLoading) return <p className="roster-state">Loading your record...</p>
  if (isRealStudent && isError) return <p className="roster-state roster-state-error">{error.message}</p>

  const guardianList = student.guardians ?? []
  const firstName = student.full_name.split(' ')[0]
  const unavailableMessage = 'This information is not available in the student portal yet.'

  return (
    <div className="student-dashboard" id="student-dashboard">
      <div className="student-dashboard-heading">
        <div>
          <p className="eyebrow">{isRealStudent ? 'Student dashboard' : 'Student dashboard preview'}</p>
          <h1>Welcome, {firstName}</h1>
          <p className="student-dashboard-subtitle">Your school day at a glance</p>
        </div>
        <div className="student-date"><CalendarDays size={15} />{TODAY_LABEL}</div>
      </div>

      <section className="student-summary" aria-label="Student overview">
        <article className="student-stat"><span className="student-stat-icon student-stat-blue"><GraduationCap size={16} /></span><div><span className="student-stat-label">Current grade</span><strong>{dash(student.grade)}</strong></div></article>
        <article className="student-stat"><span className="student-stat-icon student-stat-green"><CheckSquare size={16} /></span><div><span className="student-stat-label">Enrollment</span><strong>{dash(student.enrollment_status)}</strong></div></article>
        <article className="student-stat"><span className="student-stat-icon student-stat-amber"><BookOpen size={16} /></span><div><span className="student-stat-label">Student ID</span><strong>{dash(student.student_id)}</strong></div></article>
        <article className="student-stat"><span className="student-stat-icon student-stat-coral"><UsersRound size={16} /></span><div><span className="student-stat-label">Parents & guardians</span><strong>{guardianList.length}</strong></div></article>
      </section>

      <div className="student-dashboard-grid">
        <section className="student-panel student-panel-classes" id="student-classes">
          <div className="student-panel-heading"><div><span className="student-panel-icon"><BookOpen size={15} /></span><h2>My classes</h2></div><span className="student-panel-meta">Current year</span></div>
          <p className="student-empty-message">{unavailableMessage}</p>
        </section>

        <section className="student-panel student-panel-calendar" id="student-calendar">
          <div className="student-panel-heading"><div><span className="student-panel-icon student-panel-icon-green"><CalendarDays size={15} /></span><h2>Daily calendar</h2></div><span className="student-panel-meta">Today</span></div>
          <div className="student-empty-state"><CalendarDays size={20} /><p>{unavailableMessage}</p></div>
        </section>

        <section className="student-panel student-panel-deadlines">
          <div className="student-panel-heading"><div><span className="student-panel-icon student-panel-icon-amber"><Clock3 size={15} /></span><h2>Project deadlines</h2></div><a className="student-panel-link" href="#student-tasks" aria-label="Go to tasks and deadlines"><ArrowUpRight size={14} /></a></div>
          <div className="student-empty-state"><CheckSquare size={20} /><p>{unavailableMessage}</p></div>
        </section>

        <section className="student-panel student-panel-timetable">
          <div className="student-panel-heading"><div><span className="student-panel-icon student-panel-icon-coral"><Clock3 size={15} /></span><h2>Daily timetable</h2></div><span className="student-panel-meta">Today</span></div>
          <p className="student-empty-message">{unavailableMessage}</p>
        </section>

        <section className="student-panel student-panel-week" aria-label="Weekly timetable">
          <div className="student-panel-heading"><div><span className="student-panel-icon"><CalendarDays size={15} /></span><h2>Weekly timetable</h2></div><span className="student-panel-meta">Monday - Friday</span></div>
          <div className="student-week-empty"><Clock3 size={17} /><span>{unavailableMessage}</span></div>
        </section>

        <section className="student-panel student-panel-tasks" id="student-tasks">
          <div className="student-panel-heading"><div><span className="student-panel-icon student-panel-icon-green"><CheckSquare size={15} /></span><h2>Tasks & deadlines</h2></div><span className="student-panel-meta">Upcoming</span></div>
          <div className="student-empty-state"><CheckSquare size={20} /><p>{unavailableMessage}</p></div>
        </section>

        <section className="student-panel student-panel-record" id="student-record">
          <div className="student-panel-heading"><div><span className="student-panel-icon student-panel-icon-coral"><UsersRound size={15} /></span><h2>My record</h2></div></div>
          <div className="student-record-body">
            <div className="student-profile-name"><span>{student.full_name.split(' ').map((part) => part[0]).join('').slice(0, 2)}</span><div><strong>{student.full_name}</strong><small>{student.student_id}</small></div></div>
            <dl className="student-record-details">
              <div><dt>Khmer name</dt><dd>{dash(student.khmer_name)}</dd></div>
              <div><dt>Sex</dt><dd>{SEX_LABELS[student.sex] ?? dash(student.sex)}</dd></div>
              <div><dt>Date of birth</dt><dd>{dash(student.date_of_birth)}</dd></div>
              <div><dt>Nationality</dt><dd>{dash([student.nationality_1, student.nationality_2].filter(Boolean).join(', '))}</dd></div>
            </dl>
            <div className="student-guardians">
              <h3>Parents & guardians</h3>
              {guardianList.length === 0 ? <p className="portal-muted">No guardians on record.</p> : guardianList.map((guardian) => (
                <div className="student-guardian-row" key={`${guardian.full_name}-${guardian.relationship}`}><span>{guardian.full_name}</span><small>{guardian.relationship}</small></div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
