import { Component, OnInit, signal, Inject, PLATFORM_ID } from '@angular/core';
import { CommonModule, NgOptimizedImage, isPlatformBrowser } from '@angular/common';

@Component({
  selector: 'app-pwa-install-banner',
  standalone: true,
  imports: [CommonModule, NgOptimizedImage],
  templateUrl: './pwa-install-banner.html',
  styleUrls: ['./pwa-install-banner.scss']
})
export class PwaInstallBannerComponent implements OnInit {
  showBanner = signal(false);
  deferredPrompt: any;

  constructor(@Inject(PLATFORM_ID) private platformId: Object) {
    // Set up listener immediately to catch the beforeinstallprompt event
    if (isPlatformBrowser(this.platformId)) {
      this.setupInstallPrompt();
    }
  }

  ngOnInit(): void {
    // Additional check in case event fires after init
    if (isPlatformBrowser(this.platformId) && !this.deferredPrompt) {
      console.log('PWA Install Banner initialized and listening for beforeinstallprompt event');
    }
  }

  setupInstallPrompt(): void {
    // Listen for the beforeinstallprompt event
    window.addEventListener('beforeinstallprompt', (e: Event) => {
      console.log('beforeinstallprompt event received!');
      // Prevent the mini-infobar from appearing automatically
      e.preventDefault();
      // Store the event for later use
      this.deferredPrompt = e;
      // Show our custom banner
      this.showBanner.set(true);
      console.log('PWA install banner should now be visible');
    });

    // Handle the app successfully installed
    window.addEventListener('appinstalled', () => {
      console.log('App installed successfully');
      // Clear the deferredPrompt
      this.deferredPrompt = null;
      this.showBanner.set(false);
    });

    // Log if beforeinstallprompt doesn't fire (for debugging)
    console.log('PWA Install Banner: Listening for beforeinstallprompt event');
    console.log('Service Worker support:', 'serviceWorker' in navigator);
    console.log('Current URL:', window.location.href);
  }

  onInstallClick(): void {
    if (this.deferredPrompt) {
      // Trigger the install prompt
      this.deferredPrompt.prompt();
      // Handle the user's response to the prompt
      this.deferredPrompt.userChoice.then((choiceResult: any) => {
        if (choiceResult.outcome === 'accepted') {
          console.log('User accepted the install prompt');
        } else {
          console.log('User dismissed the install prompt');
        }
        // Clear the stored prompt
        this.deferredPrompt = null;
        this.showBanner.set(false);
      });
    }
  }

  onDismiss(): void {
    this.showBanner.set(false);
  }

  onImageLoad(event: Event): void {
    const img = event.target as HTMLImageElement;
    console.log('PWA banner icon loaded successfully:', img.src);
    img.style.opacity = '1';
  }

  onImageError(event: Event): void {
    const img = event.target as HTMLImageElement;
    console.error('Failed to load PWA banner icon from:', img.src);
    // Hide the image if it fails to load, icon is optional
    img.style.display = 'none';
  }
}
