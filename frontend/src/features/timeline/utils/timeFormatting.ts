// Time formatting utilities for timeline

/**
 * Format a time offset in seconds to a human-readable label
 * @param seconds - Seconds ago from now
 * @returns Formatted string like "30s", "2m", "1h"
 */
export function formatTimeAgo(seconds: number): string {
  if (seconds === 0) {
    return 'Now'
  }

  if (seconds < 60) {
    return `${Math.floor(seconds)}s`
  }

  if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60)
    return `${minutes}m`
  }

  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)

  if (minutes === 0) {
    return `${hours}h`
  }

  return `${hours}h${minutes}m`
}

/**
 * Format duration in milliseconds to human-readable string
 * @param ms - Duration in milliseconds
 * @returns Formatted string like "2.5s", "1m 30s", "1h 15m"
 */
export function formatDuration(ms: number): string {
  const seconds = ms / 1000

  if (seconds < 1) {
    return `${Math.round(ms)}ms`
  }

  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`
  }

  if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return secs > 0 ? `${minutes}m ${secs}s` : `${minutes}m`
  }

  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`
}

/**
 * Format a timestamp to local time string
 * @param timestamp - Unix timestamp in milliseconds
 * @returns Formatted string like "14:32:15"
 */
export function formatTimestamp(timestamp: number): string {
  return new Date(timestamp).toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

/**
 * Format a date to short format
 * @param date - Date object
 * @returns Formatted string like "Jan 15, 14:32"
 */
export function formatShortDate(date: Date): string {
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}
