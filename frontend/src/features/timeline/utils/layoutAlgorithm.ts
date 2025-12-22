// Timeline layout algorithms for overlap detection and lane assignment

import type { TimelineEvent } from '../types'

/**
 * Assigns lane indices to events to prevent overlapping
 * Uses a greedy algorithm: sort by start time, then by duration (longest first)
 * Assign each event to the first available lane
 *
 * @param events - Array of timeline events
 * @returns Map of event ID to lane index
 */
export function assignLanes(events: TimelineEvent[]): Map<string, number> {
  if (events.length === 0) {
    return new Map()
  }

  // Sort by start time, then by duration (longest first)
  const sorted = [...events].sort((a, b) => {
    const startA = a.startedAt.getTime()
    const startB = b.startedAt.getTime()

    if (startA !== startB) {
      return startA - startB
    }

    // Same start time - longer events first
    const durationA =
      (a.endedAt?.getTime() || Date.now()) - a.startedAt.getTime()
    const durationB =
      (b.endedAt?.getTime() || Date.now()) - b.startedAt.getTime()

    return durationB - durationA
  })

  const lanes: Map<string, number> = new Map()
  const laneEndTimes: number[] = [] // Track when each lane becomes free

  for (const event of sorted) {
    const eventStart = event.startedAt.getTime()
    const eventEnd = event.endedAt?.getTime() || Date.now()

    // Find first available lane
    let assignedLane = -1
    for (let i = 0; i < laneEndTimes.length; i++) {
      if (laneEndTimes[i] <= eventStart) {
        // Lane is free
        assignedLane = i
        laneEndTimes[i] = eventEnd
        break
      }
    }

    // No free lane found, create new one
    if (assignedLane === -1) {
      assignedLane = laneEndTimes.length
      laneEndTimes.push(eventEnd)
    }

    lanes.set(event.id, assignedLane)
  }

  return lanes
}

/**
 * Groups an array by a key function
 */
export function groupBy<T, K extends string | number>(
  array: T[],
  keyFn: (item: T) => K
): Map<K, T[]> {
  const map = new Map<K, T[]>()

  for (const item of array) {
    const key = keyFn(item)
    const existing = map.get(key) || []
    map.set(key, [...existing, item])
  }

  return map
}
