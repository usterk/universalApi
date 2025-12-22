/**
 * Centralized logger for frontend using Pino
 *
 * Usage:
 *   import { logger } from '@/core/utils/logger';
 *   logger.info('event_name', { key: 'value' });
 *   logger.error('error_occurred', { error: err.message });
 */

import pino from 'pino';

// Get log level from environment variable, default to 'info'
const logLevel = import.meta.env.VITE_LOG_LEVEL || 'info';

// Determine if we're in development mode
const isDevelopment = import.meta.env.DEV;

// Configure pino logger
export const logger = pino({
  level: logLevel,
  browser: {
    // Use pino-pretty for development, JSON for production
    asObject: !isDevelopment,
    serialize: !isDevelopment,
  },
  // In development, use pretty console output
  ...(isDevelopment && {
    transport: {
      target: 'pino-pretty',
      options: {
        colorize: true,
        translateTime: 'HH:MM:ss',
        ignore: 'pid,hostname',
      },
    },
  }),
});

// Export convenience methods
export const log = {
  debug: (message: string, data?: Record<string, unknown>) =>
    logger.debug(data || {}, message),

  info: (message: string, data?: Record<string, unknown>) =>
    logger.info(data || {}, message),

  warn: (message: string, data?: Record<string, unknown>) =>
    logger.warn(data || {}, message),

  error: (message: string, error?: Error | unknown, data?: Record<string, unknown>) => {
    const errorData = error instanceof Error
      ? { error: error.message, stack: error.stack, ...data }
      : { error: String(error), ...data };
    logger.error(errorData, message);
  },
};

export default logger;
