import { afterEach, describe, expect, test, vi } from 'vitest'
import { ApiError, request, setUnauthorizedHandler } from '../apiClient'

function mockFetch(status, body) {
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    text: () => Promise.resolve(body === undefined ? '' : JSON.stringify(body)),
  })
}

afterEach(() => setUnauthorizedHandler(null))

describe('request', () => {
  test('a 401 on an authenticated call triggers the unauthorized handler', async () => {
    const handler = vi.fn()
    setUnauthorizedHandler(handler)
    mockFetch(401, { detail: 'Token has expired. Please sign in again.' })

    await expect(request('/students/', {}, 'abc')).rejects.toThrow('Token has expired')
    expect(handler).toHaveBeenCalledTimes(1)
  })

  test('a 401 without a token does not trigger the handler', async () => {
    const handler = vi.fn()
    setUnauthorizedHandler(handler)
    mockFetch(401, { detail: 'nope' })

    await expect(request('/students/')).rejects.toBeInstanceOf(ApiError)
    expect(handler).not.toHaveBeenCalled()
  })

  test('field errors become a readable message', async () => {
    mockFetch(400, { first_name: ['This field is required.'] })
    await expect(request('/roster-users/', { method: 'POST' }, 't')).rejects.toThrow(
      'first_name: This field is required.',
    )
  })
})
