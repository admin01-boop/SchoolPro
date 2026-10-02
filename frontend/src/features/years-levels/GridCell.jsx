export default function GridCell({ year, track, mapping, displayName, onChange }) {
  const enabled = mapping?.is_enabled ?? false
  const label = mapping?.custom_label || displayName
  return (
    <td className={`grid-cell ${enabled ? 'cell-enabled' : ''}`}>
      <div className="cell-editor">
        <input
          className="cell-checkbox"
          type="checkbox"
          checked={enabled}
          onChange={(event) => onChange(year.id, track.id, { is_enabled: event.target.checked })}
          aria-label={`Enable ${year.name} for ${track.name}`}
        />
        <input
          className="cell-input"
          value={label}
          disabled={!enabled}
          onChange={(event) => onChange(year.id, track.id, { custom_label: event.target.value })}
          aria-label={`Custom display label for ${year.name} / ${track.name}`}
        />
      </div>
      {enabled && mapping.stats && (mapping.stats.classes > 0 || mapping.stats.students > 0) && (
        <span className="cell-stats">{mapping.stats.classes} classes - {mapping.stats.students} students</span>
      )}
    </td>
  )
}
