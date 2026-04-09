import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { AgentVerification } from '../models/agent.model';

@Injectable({
  providedIn: 'root',
})
export class AgentVerificationService {
  private apiUrl = '/api/agents';

  // Signals for verification state
  verificationStatusSignal = signal<AgentVerification | null>(null);
  isVerifyingSignal = signal<boolean>(false);
  verificationErrorSignal = signal<string | null>(null);

  // BehaviorSubjects for backward compatibility
  private verificationStatusSubject = new BehaviorSubject<AgentVerification | null>(null);
  private isVerifyingSubject = new BehaviorSubject<boolean>(false);

  public verificationStatus$ = this.verificationStatusSubject.asObservable();
  public isVerifying$ = this.isVerifyingSubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * Get agent verification status
   * FIXED: Returns Observable<AgentVerification> not array
   */
  getVerificationStatus(agentId: string): Observable<AgentVerification> {
    this.isVerifyingSignal.set(true);

    return this.http
      .get<AgentVerification>(`${this.apiUrl}/${agentId}/verification`)
      .pipe(
        tap((status) => {
          this.verificationStatusSignal.set(status);
          this.verificationStatusSubject.next(status);
          this.verificationErrorSignal.set(null);
          this.isVerifyingSignal.set(false);
        }),
        catchError((error) => {
          this.verificationErrorSignal.set(error.message);
          this.isVerifyingSignal.set(false);
          throw error;
        })
      );
  }

  /**
   * Submit verification documents
   */
  submitVerification(
    agentId: string,
    verification: {
      idNumber: string;
      idType: 'national_id' | 'passport' | 'driver_license';
      idDocument: File;
      businessRegistration?: File;
      bankStatement?: File;
    }
  ): Observable<AgentVerification> {
    const formData = new FormData();
    formData.append('idNumber', verification.idNumber);
    formData.append('idType', verification.idType);
    formData.append('idDocument', verification.idDocument);

    if (verification.businessRegistration) {
      formData.append('businessRegistration', verification.businessRegistration);
    }
    if (verification.bankStatement) {
      formData.append('bankStatement', verification.bankStatement);
    }

    this.isVerifyingSignal.set(true);

    return this.http
      .post<AgentVerification>(
        `${this.apiUrl}/${agentId}/verification/submit`,
        formData
      )
      .pipe(
        tap((result) => {
          this.verificationStatusSignal.set(result);
          this.verificationStatusSubject.next(result);
          this.verificationErrorSignal.set(null);
          this.isVerifyingSignal.set(false);
        }),
        catchError((error) => {
          this.verificationErrorSignal.set(error.message);
          this.isVerifyingSignal.set(false);
          throw error;
        })
      );
  }

  /**
   * Check verification status
   */
  isVerified(agentId: string): Observable<boolean> {
    return this.http.get<boolean>(
      `${this.apiUrl}/${agentId}/verification/is-verified`
    );
  }

  /**
   * Get verification history
   */
  getVerificationHistory(agentId: string): Observable<AgentVerification[]> {
    return this.http.get<AgentVerification[]>(
      `${this.apiUrl}/${agentId}/verification/history`
    );
  }

  /**
   * Resubmit verification after rejection
   */
  resubmitVerification(
    agentId: string,
    verification: {
      idNumber: string;
      idType: 'national_id' | 'passport' | 'driver_license';
      idDocument: File;
      businessRegistration?: File;
      bankStatement?: File;
      notes: string;
    }
  ): Observable<AgentVerification> {
    const formData = new FormData();
    formData.append('idNumber', verification.idNumber);
    formData.append('idType', verification.idType);
    formData.append('idDocument', verification.idDocument);
    formData.append('notes', verification.notes);

    if (verification.businessRegistration) {
      formData.append('businessRegistration', verification.businessRegistration);
    }
    if (verification.bankStatement) {
      formData.append('bankStatement', verification.bankStatement);
    }

    this.isVerifyingSignal.set(true);

    return this.http
      .post<AgentVerification>(
        `${this.apiUrl}/${agentId}/verification/resubmit`,
        formData
      )
      .pipe(
        tap((result) => {
          this.verificationStatusSignal.set(result);
          this.verificationStatusSubject.next(result);
          this.verificationErrorSignal.set(null);
          this.isVerifyingSignal.set(false);
        }),
        catchError((error) => {
          this.verificationErrorSignal.set(error.message);
          this.isVerifyingSignal.set(false);
          throw error;
        })
      );
  }

  /**
   * Upload single document
   */
  uploadDocument(
    agentId: string,
    documentType: 'id' | 'business' | 'bank',
    file: File
  ): Observable<{ url: string }> {
    const formData = new FormData();
    formData.append('document', file);

    return this.http.post<{ url: string }>(
      `${this.apiUrl}/${agentId}/verification/upload/${documentType}`,
      formData
    );
  }

  /**
   * Approve verification (admin only)
   */
  approveVerification(agentId: string, notes?: string): Observable<AgentVerification> {
    return this.http
      .post<AgentVerification>(
        `${this.apiUrl}/${agentId}/verification/approve`,
        { notes }
      )
      .pipe(
        tap((result) => {
          this.verificationStatusSignal.set(result);
          this.verificationStatusSubject.next(result);
        })
      );
  }

  /**
   * Reject verification (admin only)
   */
  rejectVerification(agentId: string, reason: string): Observable<AgentVerification> {
    return this.http
      .post<AgentVerification>(
        `${this.apiUrl}/${agentId}/verification/reject`,
        { reason }
      )
      .pipe(
        tap((result) => {
          this.verificationStatusSignal.set(result);
          this.verificationStatusSubject.next(result);
        })
      );
  }

  /**
   * Get verification requirements
   */
  getVerificationRequirements(): Observable<{
    idTypes: string[];
    requiredDocuments: string[];
    maxFileSize: number;
    allowedFormats: string[];
  }> {
    return this.http.get<{
      idTypes: string[];
      requiredDocuments: string[];
      maxFileSize: number;
      allowedFormats: string[];
    }>(`${this.apiUrl}/verification/requirements`);
  }

  /**
   * Get current verification status from signal
   */
  getCurrentVerificationStatus(): AgentVerification | null {
    return this.verificationStatusSignal();
  }

  /**
   * Get verification error
   */
  getVerificationError(): string | null {
    return this.verificationErrorSignal();
  }

  /**
   * Check if currently verifying
   */
  isCurrentlyVerifying(): boolean {
    return this.isVerifyingSignal();
  }

  /**
   * Clear verification error
   */
  clearError(): void {
    this.verificationErrorSignal.set(null);
  }
}
