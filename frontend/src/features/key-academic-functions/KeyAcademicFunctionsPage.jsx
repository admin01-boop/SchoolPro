import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useOutletContext } from 'react-router-dom'
import { AlertCircle, Check, ChevronDown, Menu, Save, X } from 'lucide-react'
import { request } from '@/lib/apiClient'
import UserMenu from '@/components/UserMenu'
import { useAuth } from '@/features/auth/AuthContext'

const QUERY_KEY = ['key-academic-functions']

const TERM_GRADE_OPTIONS = [
  { value: 'PERCENTAGE', label: 'Use Percentage weights' },
  { value: 'ABSOLUTE', label: 'Use Absolute weights' },
]

const YEAR_LEVEL_BEHAVIOUR_OPTIONS = [
  { value: 'MATCH_GROUP', label: 'Match Group Year Level' },
  { value: 'MATCH_IF_BLANK', label: 'Match Group Year Level if Blank' },
  { value: 'PRESERVE', label: 'Preserve Year Level' },
]

export default function KeyAcademicFunctionsPage() {
  const { token } = useAuth()
  const { openMenu } = useOutletContext()
  const queryClient = useQueryClient()
  const [configuration, setConfiguration] = useState(null)
  const [curricula, setCurricula] = useState([])
  const [notice, setNotice] = useState(null)

  const { data, isLoading, isError, error } = useQuery({
    queryKey: QUERY_KEY,
    queryFn: () => request('/key-academic-functions/', {}, token),
    enabled: Boolean(token),
  })

  useEffect(() => {
    if (!data) return
    setConfiguration(data.configuration)
    setCurricula(data.curricula)
  }, [data])

  const curriculumGroups = useMemo(() => {
    const groups = new Map()
    for (const option of curricula) {
      if (!groups.has(option.provider)) groups.set(option.provider, [])
      groups.get(option.provider).push(option)
    }
    return [...groups.entries()]
  }, [curricula])

  const saveMutation = useMutation({
    mutationFn: (payload) => request('/key-academic-functions/', {
      method: 'PUT',
      body: JSON.stringify(payload),
    }, token),
    onSuccess: (result) => {
      setConfiguration(result.configuration)
      setCurricula(result.curricula)
      setNotice({ type: 'success', text: 'Key Academic Functions have been saved.' })
      queryClient.invalidateQueries({ queryKey: QUERY_KEY })
    },
    onError: (saveError) => setNotice({ type: 'error', text: saveError.message }),
  })

  function updateConfiguration(field, value) {
    setConfiguration((current) => ({ ...current, [field]: value }))
  }

  function updateCurriculum(code, changes) {
    setCurricula((current) => current.map((option) => (
      option.code === code ? { ...option, ...changes } : option
    )))
  }

  if (isError) return <div className="loading-state">{error.message}</div>
  if (isLoading || !configuration) {
    return <div className="loading-state"><div className="spinner" />Loading academic settings...</div>
  }

  return (
    <div className="page-wrap">
      <header className="topbar">
        <button className="menu-button" onClick={openMenu} aria-label="Open navigation"><Menu size={20} /></button>
        <div className="breadcrumb"><span>Settings</span><ChevronDown size={13} /><strong>Key Academic Functions</strong></div>
        <UserMenu />
      </header>
      <main className="content">
        <div className="page-heading">
          <div><p className="eyebrow">School settings</p><h1>Key Academic Functions</h1></div>
          <div className="connection-status"><span />Connected</div>
        </div>
        <section className="settings-panel key-academic-panel">
          {notice && (
            <div className={`notice ${notice.type}`}>
              <span>{notice.type === 'success' ? <Check size={16} /> : <AlertCircle size={16} />}</span>
              {notice.text}
              <button onClick={() => setNotice(null)} aria-label="Dismiss notice"><X size={15} /></button>
            </div>
          )}

          <section className="academic-settings-section">
            <div className="academic-section-heading"><h2>Academics</h2></div>
            <div className="curriculum-groups">
              {curriculumGroups.map(([provider, options]) => (
                <section className="curriculum-group" key={provider}>
                  <h3>{provider}</h3>
                  <div className="curriculum-options">
                    {options.map((option) => (
                      <div className={`curriculum-option ${option.is_customizable && option.is_enabled ? 'curriculum-option-custom' : ''}`} key={option.id}>
                        <label className="academic-checkbox-row">
                          <input
                            type="checkbox"
                            checked={option.is_enabled}
                            onChange={(event) => updateCurriculum(option.code, { is_enabled: event.target.checked })}
                            aria-label={option.name}
                          />
                          <span>{option.name}</span>
                        </label>
                        {option.is_customizable && option.is_enabled && (
                          <div className="curriculum-label-fields">
                            <label>
                              <span>Short label</span>
                              <input
                                value={option.short_name}
                                onChange={(event) => updateCurriculum(option.code, { short_name: event.target.value })}
                                aria-label={`${option.name} short label`}
                              />
                            </label>
                            <label>
                              <span>Full title</span>
                              <input
                                value={option.full_title}
                                onChange={(event) => updateCurriculum(option.code, { full_title: event.target.value })}
                                aria-label={`${option.name} full title`}
                              />
                            </label>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </section>
              ))}
            </div>
          </section>

          <section className="academic-settings-section">
            <div className="academic-section-heading"><h2>Academics Configuration</h2></div>
            <div className="academic-settings-content">
              <fieldset className="academic-setting-group">
                <legend>Enable Key Academic Functions</legend>
                <div className="academic-inline-options">
                  <label className="academic-checkbox-row">
                    <input type="checkbox" checked={configuration.classes_enabled} onChange={(event) => updateConfiguration('classes_enabled', event.target.checked)} />
                    <span>Classes</span>
                  </label>
                  <label className="academic-checkbox-row">
                    <input type="checkbox" checked={configuration.parents_association_enabled} onChange={(event) => updateConfiguration('parents_association_enabled', event.target.checked)} />
                    <span>Parents Association</span>
                  </label>
                  <label className="academic-checkbox-row">
                    <input type="checkbox" checked={configuration.annotations_enabled} onChange={(event) => updateConfiguration('annotations_enabled', event.target.checked)} />
                    <span>Annotations</span>
                  </label>
                </div>
                <p>Enables and disables classes for all programmes except DP.</p>
              </fieldset>

              <fieldset className="academic-setting-group">
                <legend>Term Grades Calculation: Weights Options</legend>
                <div className="academic-inline-options">
                  {TERM_GRADE_OPTIONS.map((option) => (
                    <label className="academic-radio-row" key={option.value}>
                      <input
                        type="radio"
                        name="term-grade-calculation"
                        value={option.value}
                        checked={configuration.term_grade_calculation === option.value}
                        onChange={() => updateConfiguration('term_grade_calculation', option.value)}
                      />
                      <span>{option.label}</span>
                    </label>
                  ))}
                </div>
                <p>Percentage weights must total 100%. Absolute weights use values from 1 to 100.</p>
              </fieldset>

              <fieldset className="academic-setting-group">
                <legend>Term Grades Calculation: Point-based Options</legend>
                <label className="academic-checkbox-row">
                  <input type="checkbox" checked={configuration.points_based_averaging} onChange={(event) => updateConfiguration('points_based_averaging', event.target.checked)} />
                  <span>Use Points-based averaging</span>
                </label>
                <p>Uses the total points achieved divided by the maximum points available for each category.</p>
              </fieldset>

              <fieldset className="academic-setting-group">
                <legend>Year Level Behaviour</legend>
                <div className="academic-inline-options academic-inline-options-wrap">
                  {YEAR_LEVEL_BEHAVIOUR_OPTIONS.map((option) => (
                    <label className="academic-radio-row" key={option.value}>
                      <input
                        type="radio"
                        name="year-level-behaviour"
                        value={option.value}
                        checked={configuration.year_level_behaviour === option.value}
                        onChange={() => updateConfiguration('year_level_behaviour', option.value)}
                      />
                      <span>{option.label}</span>
                    </label>
                  ))}
                </div>
                <p>This setting determines how student year levels behave when switching year groups.</p>
              </fieldset>
            </div>
          </section>

          <footer className="panel-footer">
            <span className="legend"><span className="legend-dot" />Changes apply school-wide</span>
            <div className="footer-actions">
              <button className="secondary-button" onClick={() => queryClient.invalidateQueries({ queryKey: QUERY_KEY })}>Cancel</button>
              <button className="primary-button" onClick={() => saveMutation.mutate({ configuration, curricula })} disabled={saveMutation.isPending}>
                <Save size={16} />{saveMutation.isPending ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </footer>
        </section>
      </main>
    </div>
  )
}
