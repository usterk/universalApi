/**
 * Manual MSW handlers for custom test scenarios.
 *
 * These handlers take precedence over auto-generated handlers.
 * Use this file for:
 * - Error scenarios
 * - Edge cases
 * - Custom response data for specific tests
 *
 * For most cases, use the auto-generated handlers from handlers.ts
 */

import { http, HttpResponse } from 'msw'

export const manualHandlers = [
  // Example: Override login to return specific error
  // http.post('/api/v1/auth/login', () => {
  //   return HttpResponse.json(
  //     { detail: 'Invalid credentials' },
  //     { status: 401 }
  //   )
  // }),

  // Add your custom handlers here
]

// Helper to create error handlers for specific endpoints
export const createErrorHandler = (
  method: 'get' | 'post' | 'put' | 'patch' | 'delete',
  path: string,
  status: number,
  message: string
) => {
  const httpMethod = http[method]
  return httpMethod(path, () => {
    return HttpResponse.json({ detail: message }, { status })
  })
}
