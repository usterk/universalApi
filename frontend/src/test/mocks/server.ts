import { setupServer } from 'msw/node'
import { handlers } from './handlers'
import { manualHandlers } from './handlers.manual'

// Combine generated handlers with manual overrides
// Manual handlers take precedence (listed first)
export const server = setupServer(...manualHandlers, ...handlers)
