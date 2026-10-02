export const API_ROOT = '/api/v1'

let onUnauthorized = null

// AuthProvider registers this so an expired token signs the user out everywhere.
export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler
}

export class ApiError extends Error {
  constructor(message, status, body) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

// DRF errors are {detail} or {field: [messages]}; flatten to one readable string.
function describeError(text, status) {
  const fallback = `Request failed with status ${status}`
  if (!text) return fallback
  let body
  try {
    body = JSON.parse(text)
  } catch {
    return text
  }
  if (typeof body === 'string') return body
  if (body?.detail) return String(body.detail)
  if (body && typeof body === 'object') {
    const lines = Object.entries(body).map(([field, value]) => {
      const message = Array.isArray(value) ? value.join(' ') : typeof value === 'object' ? JSON.stringify(value) : String(value)
      return field === 'non_field_errors' ? message : `${field}: ${message}`
    })
    if (lines.length) return lines.join('\n')
  }
  return fallback
}

export async function request(path, options = {}, token) {
  const response = await fetch(`${API_ROOT}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Token ${token}` } : {}),
      ...options.headers,
    },
  })
  const text = await response.text()
  if (response.status === 401 && token && onUnauthorized) onUnauthorized()
  if (!response.ok) throw new ApiError(describeError(text, response.status), response.status, text)
  return text ? JSON.parse(text) : null
}
