#!/usr/bin/env tsx
/**
 * MSW Mock Handler Generator from OpenAPI Schema
 *
 * This script fetches the OpenAPI schema from the backend and generates
 * MSW handlers for all endpoints. Run with:
 *
 *   npm run generate:mocks
 *
 * Prerequisites:
 *   - Backend must be running on http://localhost:8000
 *   - tsx must be installed: npm install -D tsx
 */

import * as fs from 'fs'
import * as path from 'path'

const OPENAPI_URL = 'http://localhost:8000/api/openapi.json'
const OUTPUT_PATH = path.join(__dirname, '../src/test/mocks/handlers.ts')

interface OpenAPIPath {
  [method: string]: {
    operationId?: string
    summary?: string
    tags?: string[]
    requestBody?: {
      content?: {
        [mediaType: string]: {
          schema?: OpenAPISchema
        }
      }
    }
    responses?: {
      [statusCode: string]: {
        content?: {
          [mediaType: string]: {
            schema?: OpenAPISchema
          }
        }
      }
    }
    parameters?: Array<{
      name: string
      in: 'path' | 'query' | 'header'
      required?: boolean
      schema?: OpenAPISchema
    }>
    security?: Array<{ [key: string]: string[] }>
  }
}

interface OpenAPISchema {
  type?: string
  properties?: { [key: string]: OpenAPISchema }
  items?: OpenAPISchema
  $ref?: string
  enum?: string[]
  format?: string
  required?: string[]
  anyOf?: OpenAPISchema[]
  allOf?: OpenAPISchema[]
}

interface OpenAPISpec {
  openapi: string
  info: { title: string; version: string }
  paths: { [path: string]: OpenAPIPath }
  components?: {
    schemas?: { [name: string]: OpenAPISchema }
    securitySchemes?: { [name: string]: unknown }
  }
}

// Generate mock value based on schema
function generateMockValue(schema: OpenAPISchema, schemas: { [name: string]: OpenAPISchema } = {}): unknown {
  if (schema.$ref) {
    const refName = schema.$ref.split('/').pop()!
    if (schemas[refName]) {
      return generateMockValue(schemas[refName], schemas)
    }
    return {}
  }

  if (schema.anyOf || schema.allOf) {
    const subSchemas = schema.anyOf || schema.allOf || []
    if (subSchemas.length > 0) {
      return generateMockValue(subSchemas[0], schemas)
    }
  }

  if (schema.enum && schema.enum.length > 0) {
    return schema.enum[0]
  }

  switch (schema.type) {
    case 'string':
      if (schema.format === 'date-time') return '2024-01-01T00:00:00Z'
      if (schema.format === 'uuid') return 'mock-uuid-' + Math.random().toString(36).slice(2, 9)
      if (schema.format === 'email') return 'test@example.com'
      if (schema.format === 'uri') return 'https://example.com'
      return 'mock-string'

    case 'integer':
    case 'number':
      return 1

    case 'boolean':
      return true

    case 'array':
      if (schema.items) {
        return [generateMockValue(schema.items, schemas)]
      }
      return []

    case 'object':
      if (schema.properties) {
        const obj: { [key: string]: unknown } = {}
        for (const [key, propSchema] of Object.entries(schema.properties)) {
          obj[key] = generateMockValue(propSchema, schemas)
        }
        return obj
      }
      return {}

    default:
      return null
  }
}

// Convert OpenAPI path to MSW path pattern
function convertPath(path: string): string {
  // Convert {param} to :param
  return path.replace(/\{([^}]+)\}/g, ':$1')
}

// Generate handler code for an endpoint
function generateHandler(
  path: string,
  method: string,
  operation: OpenAPIPath[string],
  schemas: { [name: string]: OpenAPISchema }
): string {
  const mswPath = convertPath(path)
  const httpMethod = method.toLowerCase()
  const hasAuth = operation.security && operation.security.length > 0

  // Get success response schema
  let responseSchema: OpenAPISchema | undefined
  let successStatus = '200'

  for (const status of ['200', '201', '204']) {
    if (operation.responses?.[status]) {
      successStatus = status
      const content = operation.responses[status].content
      if (content?.['application/json']?.schema) {
        responseSchema = content['application/json'].schema
      }
      break
    }
  }

  const mockResponse = responseSchema ? generateMockValue(responseSchema, schemas) : null

  // Build handler
  let handlerCode = `  // ${method.toUpperCase()} ${path}\n`
  handlerCode += `  http.${httpMethod}('${mswPath}', ({ request`

  // Add params if path has parameters
  if (path.includes('{')) {
    handlerCode += ', params'
  }

  handlerCode += ` }) => {\n`

  // Add auth check
  if (hasAuth) {
    handlerCode += `    const authHeader = request.headers.get('Authorization')\n`
    handlerCode += `    if (!authHeader) {\n`
    handlerCode += `      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })\n`
    handlerCode += `    }\n\n`
  }

  // Add response
  if (successStatus === '204') {
    handlerCode += `    return new HttpResponse(null, { status: 204 })\n`
  } else if (mockResponse !== null) {
    const responseJson = JSON.stringify(mockResponse, null, 6).replace(/\n/g, '\n    ')
    handlerCode += `    return HttpResponse.json(${responseJson})\n`
  } else {
    handlerCode += `    return HttpResponse.json({})\n`
  }

  handlerCode += `  }),\n`

  return handlerCode
}

async function main() {
  console.log('Fetching OpenAPI schema from', OPENAPI_URL)

  let spec: OpenAPISpec

  try {
    const response = await fetch(OPENAPI_URL)
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    spec = await response.json() as OpenAPISpec
  } catch (error) {
    console.error('Failed to fetch OpenAPI schema. Is the backend running?')
    console.error('Error:', error)
    console.error('\nMake sure to start the backend first:')
    console.error('  make start-all')
    console.error('  # or')
    console.error('  make backend-start')
    process.exit(1)
  }

  console.log(`Found ${Object.keys(spec.paths).length} paths in OpenAPI schema`)

  const schemas = spec.components?.schemas || {}

  // Group handlers by tag
  const handlersByTag: { [tag: string]: string[] } = {}

  for (const [path, methods] of Object.entries(spec.paths)) {
    for (const [method, operation] of Object.entries(methods)) {
      if (['get', 'post', 'put', 'patch', 'delete'].includes(method)) {
        const tag = operation.tags?.[0] || 'default'
        if (!handlersByTag[tag]) {
          handlersByTag[tag] = []
        }
        handlersByTag[tag].push(generateHandler(path, method, operation, schemas))
      }
    }
  }

  // Generate output file
  let output = `/**
 * AUTO-GENERATED MSW handlers from OpenAPI schema.
 *
 * DO NOT EDIT THIS FILE MANUALLY!
 * Run \`npm run generate:mocks\` to regenerate from /api/openapi.json
 *
 * For custom handlers, use handlers.manual.ts instead.
 *
 * Generated at: ${new Date().toISOString()}
 * OpenAPI version: ${spec.info.version}
 */

import { http, HttpResponse } from 'msw'

`

  for (const [tag, handlers] of Object.entries(handlersByTag)) {
    const tagName = tag.charAt(0).toUpperCase() + tag.slice(1).replace(/-/g, ' ')
    output += `// ============================================================================\n`
    output += `// ${tagName} Handlers\n`
    output += `// ============================================================================\n\n`
    output += `const ${tag.replace(/-/g, '')}Handlers = [\n`
    output += handlers.join('\n')
    output += `]\n\n`
  }

  // Export all handlers
  output += `// ============================================================================\n`
  output += `// Export all handlers\n`
  output += `// ============================================================================\n\n`
  output += `export const handlers = [\n`
  for (const tag of Object.keys(handlersByTag)) {
    output += `  ...${tag.replace(/-/g, '')}Handlers,\n`
  }
  output += `]\n`

  // Write output
  fs.writeFileSync(OUTPUT_PATH, output)
  console.log(`Generated handlers at ${OUTPUT_PATH}`)
  console.log(`Total handlers: ${Object.values(handlersByTag).flat().length}`)
}

main().catch(console.error)
