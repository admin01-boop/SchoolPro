import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useOutletContext } from 'react-router-dom'
import { AlertCircle, Check, ChevronDown, Menu, Save, X } from 'lucide-react'
import { request } from '@/lib/apiClient'
import UserMenu from '@/components/UserMenu'
import { useAuth } from '@/features/auth/AuthContext'
import GridCell from './GridCell'

const GRID_QUERY_KEY = ['years-levels-grid']

export default function YearsLevelsPage() {
  const { token } = useAuth()
  const { openMenu } = useOutletContext()
  const queryClient = useQueryClient()
  const [academicYearId, setAcademicYearId] = useState('')

  const { data, isLoading, isError, error: loadError } = useQuery({
    queryKey: [...GRID_QUERY_KEY, academicYearId],
    queryFn: () => request(
      `/years-levels-grid/${academicYearId ? `?academic_year=${academicYearId}` : ''}`,
      {},
      token,
    ),
    enabled: Boolean(token),
  })

  const selectedAcademicYearId = academicYearId || String(data?.selected_academic_year ?? '')
  const [format, setFormat] = useState('YEAR_12_13')
  const [mappings, setMappings] = useState({})
  const [notice, setNotice] = useState(null)

  useEffect(() => {
    if (!data) return
    setFormat(data.grade_numbering_format)
    setMappings(data.mappings)
  }, [data])

  const tracks = useMemo(
    () => data?.frameworks.flatMap((framework) => framework.tracks.map((track) => ({ ...track, frameworkId: framework.id }))) ?? [],
    [data],
  )

  function updateCell(yearId, trackId, changes) {
    const key = `${yearId}:${trackId}`
    setMappings((current) => ({ ...current, [key]: { ...(current[key] ?? { is_enabled: false, custom_label: '' }), ...changes } }))
  }

  const saveMutation = useMutation({
    mutationFn: (payload) => request('/years-levels-grid/', {
      method: 'PUT',
      body: JSON.stringify(payload),
    }, token),
    onSuccess: () => {
      setNotice({ type: 'success', text: 'Your Years & Levels settings have been saved.' })
      queryClient.invalidateQueries({ queryKey: GRID_QUERY_KEY })
    },
    onError: (mutationError) => setNotice({ type: 'error', text: mutationError.message }),
  })

  function saveChanges() {
    saveMutation.mutate({
      academic_year: Number(data.selected_academic_year || selectedAcademicYearId),
      grade_numbering_format: format,
      mappings: Object.entries(mappings).map(([key, mapping]) => {
        const [yearId, trackId] = key.split(':')
        return {
          year_level: Number(yearId),
          track: Number(trackId),
          is_enabled: mapping.is_enabled,
          custom_label: mapping.custom_label ?? '',
        }
      }),
    })
  }

  if (isLoading || !data) return <div className="loading-state"><div className="spinner" />Loading Years & Levels...</div>
  if (isError) return <div className="loading-state">{loadError.message}</div>

  return (
    <div className="page-wrap">
      <header className="topbar">
        <button className="menu-button" onClick={openMenu} aria-label="Open navigation"><Menu size={20} /></button>
        <div className="breadcrumb"><span>Settings</span><ChevronDown size={13} /><strong>School Settings: Years & Levels</strong></div>
        <UserMenu />
      </header>
      <main className="content grades-levels-content">
        <div className="page-heading"><div><p className="eyebrow">School settings</p><h1 className="grades-levels-title">Grades & Levels</h1></div><div className="connection-status"><span />Connected</div></div>
        <section className="settings-panel grades-levels-panel">
          <div className="panel-heading">
            <div><h2>Grades & Levels Overview</h2><p>Configure the year levels offered under each curriculum.</p></div>
            <div className="settings-controls">
              <label className="format-control">
                <span>Academic year</span>
                <select value={selectedAcademicYearId} onChange={(event) => setAcademicYearId(event.target.value)}>
                  {data.academic_years.map((year) => <option key={year.id} value={year.id}>{year.name}{year.is_current ? ' (Current)' : ''}</option>)}
                </select>
              </label>
              <div className="format-control">
                <span>Grade & Year Format</span>
                <div className="radio-group">
                  <label><input type="radio" checked={format === 'GRADE_11_12'} onChange={() => setFormat('GRADE_11_12')} />Grade 11 & 12</label>
                  <label><input type="radio" checked={format === 'YEAR_12_13'} onChange={() => setFormat('YEAR_12_13')} />Year 12 & 13</label>
                </div>
              </div>
            </div>
          </div>
          {notice && (
            <div className={`notice ${notice.type}`}>
              <span>{notice.type === 'success' ? <Check size={16} /> : <AlertCircle size={16} />}</span>
              {notice.text}
              <button onClick={() => setNotice(null)} aria-label="Dismiss notice"><X size={15} /></button>
            </div>
          )}
          <div className="table-scroll">
            <table className="levels-table" style={{ width: `${130 + tracks.length * 105}px` }}>
              <thead>
                <tr>
                  <th className="year-heading" rowSpan="2">Year level</th>
                  {data.frameworks.map((framework) => <th colSpan={framework.tracks.length} key={framework.id}>{framework.name}</th>)}
                </tr>
                <tr>
                  {data.frameworks.flatMap((framework) => framework.tracks.map((track) => <th className="track-heading" key={track.id}>{track.name}</th>))}
                </tr>
              </thead>
              <tbody>
                {data.year_levels.map((year) => (
                  <tr key={year.id}>
                    <th className="year-label">{format === 'GRADE_11_12' ? year.grade_display_name : year.name}</th>
                    {tracks.map((track) => (
                      <GridCell
                        key={`${year.id}:${track.id}`}
                        year={year}
                        track={track}
                        mapping={mappings[`${year.id}:${track.id}`]}
                        displayName={format === 'GRADE_11_12' ? year.grade_display_name : year.name}
                        onChange={updateCell}
                      />
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <footer className="panel-footer">
            <div className="footer-actions">
              <button className="secondary-button" onClick={() => queryClient.invalidateQueries({ queryKey: GRID_QUERY_KEY })}>Cancel</button>
              <button className="primary-button" onClick={saveChanges} disabled={saveMutation.isPending || (!academicYearId && !data.selected_academic_year)}>
                <Save size={16} />{saveMutation.isPending ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </footer>
        </section>
      </main>
    </div>
  )
}
