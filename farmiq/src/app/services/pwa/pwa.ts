/**
 * FarmIQ PWA Installation & Notification Service
 * Handles PWA installation prompts, service worker registration, and notifications
 * 
 * Usage in component:
 * constructor(private pwaService: Pwa) {}
 * 
 * ngOnInit() {
 *   this.pwaService.checkInstallPrompt();
 *   this.pwaService.isInstalled$.subscribe(installed => {
 *     console.log('App installed:', installed);
 *   });
 * }
 */

import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

declare global {
  interface Window {
    deferredPrompt?: BeforeInstallPromptEvent;
  }
}

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

@Injectable({
  providedIn: 'root',
})
export class Pwa {
  private isInstalledSubject = new BehaviorSubject<boolean>(this.checkIfInstalled());
  private isOnlineSubject = new BehaviorSubject<boolean>(navigator.onLine);
  private installPromptSubject = new BehaviorSubject<BeforeInstallPromptEvent | null>(null);

  readonly isInstalled$ = this.isInstalledSubject.asObservable();
  readonly isOnline$ = this.isOnlineSubject.asObservable();
  readonly installPrompt$ = this.installPromptSubject.asObservable();

  constructor() {
    this.initializeListeners();
    this.registerServiceWorker();
  }

  /**
   * Initialize PWA-related event listeners
   */
  private initializeListeners(): void {
    // Listen for beforeinstallprompt event
    window.addEventListener('beforeinstallprompt', (event: any) => {
      event.preventDefault();
      this.installPromptSubject.next(event);
    });

    // Listen for app installed event
    window.addEventListener('appinstalled', () => {
      this.isInstalledSubject.next(true);
      console.log('FarmIQ PWA installed successfully');
    });

    // Listen for online/offline status
    window.addEventListener('online', () => {
      this.isOnlineSubject.next(true);
      console.log('App is back online');
    });

    window.addEventListener('offline', () => {
      this.isOnlineSubject.next(false);
      console.log('App is offline');
    });
  }

  /**
   * Register the service worker
   */
  private registerServiceWorker(): void {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker
        .register('/ngsw-worker.js', { scope: '/' })
        .then(registration => {
          console.log('Service Worker registered:', registration);
          this.checkForUpdates(registration);
        })
        .catch(error => {
          console.error('Service Worker registration failed:', error);
        });
    }
  }

  /**
   * Check for service worker updates every 30 minutes
   */
  private checkForUpdates(registration: ServiceWorkerRegistration): void {
    setInterval(() => {
      registration.update();
    }, 30 * 60 * 1000); // Check every 30 minutes
  }

  /**
   * Check if app is installed (different methods for different platforms)
   */
  private checkIfInstalled(): boolean {
    // Check if running as PWA on iOS
    if (this.isRunningOnIOSPWA()) {
      return true;
    }

    // Check if running as standalone
    if (window.matchMedia('(display-mode: standalone)').matches) {
      return true;
    }

    // Check for standalone mode cookie
    return document.cookie.includes('pwa_installed=true');
  }

  /**
   * Detect if running as PWA on iOS
   */
  private isRunningOnIOSPWA(): boolean {
    const nav = window.navigator as any;
    return (
      nav.standalone === true ||
      (nav.standalone !== undefined && nav.standalone === true)
    );
  }

  /**
   * Show install prompt to user
   */
  async showInstallPrompt(): Promise<boolean> {
    const deferredPrompt = this.installPromptSubject.value;
    if (!deferredPrompt) {
      console.warn('Install prompt not available');
      return false;
    }

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    
    if (outcome === 'accepted') {
      this.installPromptSubject.next(null);
      this.isInstalledSubject.next(true);
      return true;
    }
    
    return false;
  }

  /**
   * Check if install prompt is available
   */
  isInstallPromptAvailable(): boolean {
    return this.installPromptSubject.value !== null;
  }

  /**
   * Get current online status
   */
  isOnline(): boolean {
    return this.isOnlineSubject.value;
  }

  /**
   * Get current installed status
   */
  isInstalledApp(): boolean {
    return this.isInstalledSubject.value;
  }

  /**
   * Request notification permission
   */
  async requestNotificationPermission(): Promise<NotificationPermission> {
    if ('Notification' in window) {
      return Notification.requestPermission();
    }
    return 'denied';
  }

  /**
   * Show a notification
   */
  async showNotification(
    title: string,
    options?: NotificationOptions
  ): Promise<void> {
    if ('serviceWorker' in navigator && 'ready' in navigator.serviceWorker) {
      const registration = await navigator.serviceWorker.ready;
      registration.showNotification(title, {
        icon: '/icons/apple-touch-icon.png',
        badge: '/icons/apple-touch-icon.png',
        ...options
      });
    }
  }

  /**
   * Send a notification with action buttons
   */
  async sendNotificationWithActions(
    title: string,
    message: string,
    actions: object[]
  ): Promise<void> {
    await this.showNotification(title, {
      body: message,
      tag: 'farmiq-notification'
    } as NotificationOptions);
  }

  /**
   * Get device orientation
   */
  getOrientation(): 'portrait' | 'landscape' {
    return window.innerHeight > window.innerWidth ? 'portrait' : 'landscape';
  }

  /**
   * Lock orientation (if supported)
   */
  async lockOrientation(orientation: OrientationLockType): Promise<boolean> {
    if ('orientation' in screen && 'lock' in (screen as any).orientation) {
      try {
        await (screen as any).orientation.lock(orientation);
        return true;
      } catch (error) {
        console.error('Failed to lock orientation:', error);
        return false;
      }
    }
    return false;
  }

  /**
   * Unlock orientation
   */
  async unlockOrientation(): Promise<boolean> {
    if ('orientation' in screen && 'unlock' in (screen as any).orientation) {
      try {
        (screen as any).orientation.unlock();
        return true;
      } catch (error) {
        console.error('Failed to unlock orientation:', error);
        return false;
      }
    }
    return false;
  }

  /**
   * Check if device is iOS
   */
  isIOS(): boolean {
    return /iPad|iPhone|iPod/.test(navigator.userAgent);
  }

  /**
   * Check if device is Android
   */
  isAndroid(): boolean {
    return /Android/.test(navigator.userAgent);
  }

  /**
   * Get device type
   */
  getDeviceType(): 'ios' | 'android' | 'desktop' {
    if (this.isIOS()) return 'ios';
    if (this.isAndroid()) return 'android';
    return 'desktop';
  }

  /**
   * Trigger haptic feedback if available
   */
  triggerHapticFeedback(type: 'light' | 'medium' | 'heavy' = 'medium'): void {
    if ('vibrate' in navigator) {
      const patterns: Record<string, number | number[]> = {
        light: 10,
        medium: 20,
        heavy: 30
      };
      navigator.vibrate(patterns[type] || 20);
    }
  }

  /**
   * Request camera permission
   */
  async requestCameraPermission(): Promise<boolean> {
    try {
      await navigator.mediaDevices.getUserMedia({ video: true });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Request microphone permission
   */
  async requestMicrophonePermission(): Promise<boolean> {
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get device storage quota
   */
  async getStorageInfo(): Promise<StorageEstimate> {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      return navigator.storage.estimate();
    }
    return { usage: 0, quota: 0 };
  }

  /**
   * Request persistent storage
   */
  async requestPersistentStorage(): Promise<boolean> {
    if ('storage' in navigator && 'persist' in navigator.storage) {
      return navigator.storage.persist();
    }
    return false;
  }

  /**
   * Clear cache
   */
  async clearCache(): Promise<void> {
    if ('caches' in window) {
      const cacheNames = await caches.keys();
      await Promise.all(
        cacheNames.map(cacheName => caches.delete(cacheName))
      );
      console.log('Cache cleared');
    }
  }

  /**
   * Get safe area insets (for iOS notch/dynamic island)
   */
  getSafeAreaInsets(): SafeAreaInsets {
    return {
      top: this.getCSSVariableValue('--safe-area-inset-top'),
      right: this.getCSSVariableValue('--safe-area-inset-right'),
      bottom: this.getCSSVariableValue('--safe-area-inset-bottom'),
      left: this.getCSSVariableValue('--safe-area-inset-left')
    };
  }

  /**
   * Helper to get CSS variable value
   */
  private getCSSVariableValue(variableName: string): string {
    return getComputedStyle(document.documentElement)
      .getPropertyValue(variableName)
      .trim();
  }
}

// Type definitions
export interface SafeAreaInsets {
  top: string;
  right: string;
  bottom: string;
  left: string;
}

type OrientationLockType =
  | 'portrait'
  | 'portrait-primary'
  | 'portrait-secondary'
  | 'landscape'
  | 'landscape-primary'
  | 'landscape-secondary'
  | 'any';
