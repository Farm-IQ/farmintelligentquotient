import { Injectable, signal } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';

/**
 * Error Types for categorization
 */
export enum ErrorType {
  HTTP = 'HTTP',
  AUTH = 'AUTH',
  VALIDATION = 'VALIDATION',
  NETWORK = 'NETWORK',
  UNKNOWN = 'UNKNOWN',
  SUPABASE = 'SUPABASE',
}

/**
 * Error Severity for user-facing notifications
 */
export enum ErrorSeverity {
  ERROR = 'error',
  WARNING = 'warning',
  INFO = 'info',
}

/**
 * Structured error object
 */
export interface AppError {
  type: ErrorType;
  severity: ErrorSeverity;
  message: string;
  userMessage: string;
  statusCode?: number;
  timestamp: Date;
  context?: any;
  stackTrace?: string;
}

/**
 * Centralized Error Handling Service
 * Handles error transformation, logging, and user notifications
 */
@Injectable({
  providedIn: 'root',
})
export class ErrorHandlingService {
  // Signal for current error state
  private currentErrorSignal = signal<AppError | null>(null);
  public currentError$ = this.currentErrorSignal.asReadonly();

  // Error history for debugging
  private errorHistorySignal = signal<AppError[]>([]);
  public errorHistory$ = this.errorHistorySignal.asReadonly();

  // Maximum errors to keep in history
  private readonly MAX_ERROR_HISTORY = 50;

  constructor() {
    this.initializeGlobalErrorListener();
  }

  /**
   * Initialize global error listener for uncaught errors
   */
  private initializeGlobalErrorListener(): void {
    if (typeof window !== 'undefined') {
      window.addEventListener('error', (event: ErrorEvent) => {
        this.handleError(
          new Error(event.message),
          ErrorType.UNKNOWN,
          { filename: event.filename, lineno: event.lineno }
        );
      });

      window.addEventListener('unhandledrejection', (event: PromiseRejectionEvent) => {
        this.handleError(event.reason, ErrorType.UNKNOWN);
      });
    }
  }

  /**
   * Main error handling method
   * Transforms various error types into structured AppError
   */
  handleError(
    error: any,
    type: ErrorType = ErrorType.UNKNOWN,
    context?: any
  ): AppError {
    let appError: AppError;

    if (error instanceof HttpErrorResponse) {
      appError = this.handleHttpError(error, context);
    } else if (error instanceof Error) {
      appError = this.handleTypeError(error, type, context);
    } else if (typeof error === 'string') {
      appError = this.createAppError(
        type,
        error,
        error,
        ErrorSeverity.ERROR,
        context
      );
    } else {
      appError = this.createAppError(
        ErrorType.UNKNOWN,
        'An unexpected error occurred',
        'Something went wrong. Please try again.',
        ErrorSeverity.ERROR,
        error
      );
    }

    this.logError(appError);
    this.currentErrorSignal.set(appError);
    this.addToHistory(appError);

    return appError;
  }

  /**
   * Handle HTTP errors specifically
   */
  private handleHttpError(error: HttpErrorResponse, context?: any): AppError {
    const statusCode = error.status;
    let type = ErrorType.HTTP;
    let severity = ErrorSeverity.ERROR;
    let userMessage = this.getHttpErrorMessage(statusCode);
    let message = error.message || `HTTP Error ${statusCode}`;

    // Check error body for more details
    if (error.error) {
      if (typeof error.error === 'string') {
        message = error.error;
      } else if (error.error.message) {
        message = error.error.message;
      } else if (error.error.error) {
        message = error.error.error;
      }
    }

    // Categorize by status code
    if (statusCode === 401) {
      type = ErrorType.AUTH;
      userMessage = 'Your session has expired. Please log in again.';
    } else if (statusCode === 403) {
      type = ErrorType.AUTH;
      userMessage = 'You do not have permission to perform this action.';
    } else if (statusCode === 422) {
      type = ErrorType.VALIDATION;
      userMessage = error.error?.message || 'Please check your input and try again.';
    } else if (statusCode === 0) {
      type = ErrorType.NETWORK;
      userMessage = 'Network connection failed. Please check your internet connection.';
    }

    return this.createAppError(
      type,
      message,
      userMessage,
      severity,
      { statusCode, ...context }
    );
  }

  /**
   * Handle regular TypeScript errors
   */
  private handleTypeError(
    error: Error,
    type: ErrorType,
    context?: any
  ): AppError {
    const userMessage = this.getUserFriendlyMessage(type);
    return this.createAppError(
      type,
      error.message,
      userMessage,
      ErrorSeverity.ERROR,
      context,
      error.stack
    );
  }

  /**
   * Create structured AppError object
   */
  private createAppError(
    type: ErrorType,
    message: string,
    userMessage: string,
    severity: ErrorSeverity,
    context?: any,
    stackTrace?: string
  ): AppError {
    return {
      type,
      severity,
      message,
      userMessage,
      timestamp: new Date(),
      context,
      stackTrace,
    };
  }

  /**
   * Get user-friendly message based on error type
   */
  private getUserFriendlyMessage(type: ErrorType): string {
    const messages: Record<ErrorType, string> = {
      [ErrorType.HTTP]: 'A server error occurred. Please try again.',
      [ErrorType.AUTH]: 'Authentication failed. Please log in again.',
      [ErrorType.VALIDATION]: 'Please check your input and try again.',
      [ErrorType.NETWORK]: 'Network error. Please check your connection.',
      [ErrorType.SUPABASE]: 'Database error. Please try again.',
      [ErrorType.UNKNOWN]: 'An unexpected error occurred. Please try again.',
    };
    return messages[type] || messages[ErrorType.UNKNOWN];
  }

  /**
   * Get user-friendly message based on HTTP status code
   */
  private getHttpErrorMessage(statusCode: number): string {
    const messages: Record<number, string> = {
      400: 'Bad request. Please check your input.',
      401: 'Your session has expired. Please log in again.',
      403: 'You do not have permission to access this resource.',
      404: 'The requested resource was not found.',
      409: 'This resource already exists or there is a conflict.',
      422: 'Please check your input and try again.',
      429: 'Too many requests. Please wait a moment and try again.',
      500: 'Server error. Please try again later.',
      502: 'Service temporarily unavailable. Please try again later.',
      503: 'Service is down for maintenance. Please try again later.',
      504: 'Request timeout. Please try again.',
    };
    return messages[statusCode] || 'An error occurred. Please try again.';
  }

  /**
   * Log error to console and optionally to remote logging service
   */
  private logError(error: AppError): void {
    // Log to console in development
    if (typeof window !== 'undefined' && !this.isProduction()) {
      console.group(`🚨 ${error.type} Error`);
      console.error('Message:', error.message);
      console.error('User Message:', error.userMessage);
      console.error('Severity:', error.severity);
      console.error('Timestamp:', error.timestamp);
      if (error.context) {
        console.error('Context:', error.context);
      }
      if (error.stackTrace) {
        console.error('Stack Trace:', error.stackTrace);
      }
      console.groupEnd();
    }

    // TODO: Send to remote logging service (e.g., Sentry, LogRocket)
    // this.sendToRemoteLogger(error);
  }

  /**
   * Add error to history for debugging
   */
  private addToHistory(error: AppError): void {
    const history = this.errorHistorySignal();
    const updatedHistory = [error, ...history];

    // Keep only the last MAX_ERROR_HISTORY errors
    if (updatedHistory.length > this.MAX_ERROR_HISTORY) {
      updatedHistory.pop();
    }

    this.errorHistorySignal.set(updatedHistory);
  }

  /**
   * Clear current error
   */
  clearCurrentError(): void {
    this.currentErrorSignal.set(null);
  }

  /**
   * Clear all error history
   */
  clearErrorHistory(): void {
    this.errorHistorySignal.set([]);
  }

  /**
   * Get current error
   */
  getCurrentError(): AppError | null {
    return this.currentErrorSignal();
  }

  /**
   * Get error history
   */
  getErrorHistory(): AppError[] {
    return this.errorHistorySignal();
  }

  /**
   * Check if running in production
   */
  private isProduction(): boolean {
    try {
      const environment = require('../../environments/environment');
      return environment.environment?.production || false;
    } catch {
      return false;
    }
  }
}
