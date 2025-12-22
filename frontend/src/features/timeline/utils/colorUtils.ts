// Color utility functions for timeline

import type { JobStatus } from '../types'

/**
 * Get color for job status
 * @param status - Job status
 * @param pluginColor - Base plugin color
 * @returns CSS color string
 */
export function getStatusColor(status: JobStatus, pluginColor: string): string {
  switch (status) {
    case 'failed':
      return '#EF4444' // red-500
    case 'completed':
      return pluginColor
    case 'running':
      return addAlpha(pluginColor, 0.6) // 60% opacity for running
    default:
      return pluginColor
  }
}

/**
 * Add alpha (opacity) to a hex color
 * @param hexColor - Hex color like "#6366F1"
 * @param alpha - Alpha value 0-1
 * @returns Hex color with alpha like "#6366F199"
 */
export function addAlpha(hexColor: string, alpha: number): string {
  // Remove # if present
  const hex = hexColor.replace('#', '')

  // Convert alpha to hex (0-255)
  const alphaHex = Math.round(alpha * 255)
    .toString(16)
    .padStart(2, '0')

  return `#${hex}${alphaHex}`
}

/**
 * Convert hex color to RGB
 * @param hexColor - Hex color like "#6366F1"
 * @returns Object with r, g, b values
 */
export function hexToRgb(hexColor: string): { r: number; g: number; b: number } | null {
  const hex = hexColor.replace('#', '')

  if (hex.length === 3) {
    const r = parseInt(hex[0] + hex[0], 16)
    const g = parseInt(hex[1] + hex[1], 16)
    const b = parseInt(hex[2] + hex[2], 16)
    return { r, g, b }
  }

  if (hex.length === 6) {
    const r = parseInt(hex.substring(0, 2), 16)
    const g = parseInt(hex.substring(2, 4), 16)
    const b = parseInt(hex.substring(4, 6), 16)
    return { r, g, b }
  }

  return null
}

/**
 * Check if a color is light or dark
 * @param hexColor - Hex color like "#6366F1"
 * @returns true if light, false if dark
 */
export function isLightColor(hexColor: string): boolean {
  const rgb = hexToRgb(hexColor)
  if (!rgb) return false

  // Calculate relative luminance
  const luminance = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255

  return luminance > 0.5
}
