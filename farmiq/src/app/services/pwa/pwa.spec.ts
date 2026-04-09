import { TestBed } from '@angular/core/testing';

import { Pwa } from './pwa';

describe('Pwa Service', () => {
  let service: Pwa;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Pwa);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('Installation Detection', () => {
    it('should detect if app is installed', () => {
      const isInstalled = service.isInstalledApp();
      expect(typeof isInstalled).toBe('boolean');
    });

    it('should provide isInstalled$ observable', (done) => {
      service.isInstalled$.subscribe(installed => {
        expect(typeof installed).toBe('boolean');
        done();
      });
    });
  });

  describe('Online Status', () => {
    it('should provide online status', () => {
      const isOnline = service.isOnline();
      expect(typeof isOnline).toBe('boolean');
    });

    it('should provide isOnline$ observable', (done) => {
      service.isOnline$.subscribe(online => {
        expect(typeof online).toBe('boolean');
        done();
      });
    });
  });

  describe('Device Detection', () => {
    it('should detect device type', () => {
      const deviceType = service.getDeviceType();
      expect(['ios', 'android', 'desktop']).toContain(deviceType);
    });

    it('should have iOS detection method', () => {
      const isIOS = service.isIOS();
      expect(typeof isIOS).toBe('boolean');
    });

    it('should have Android detection method', () => {
      const isAndroid = service.isAndroid();
      expect(typeof isAndroid).toBe('boolean');
    });
  });

  describe('Orientation', () => {
    it('should detect orientation', () => {
      const orientation = service.getOrientation();
      expect(['portrait', 'landscape']).toContain(orientation);
    });
  });

  describe('Safe Area Insets', () => {
    it('should get safe area insets', () => {
      const insets = service.getSafeAreaInsets();
      expect(insets).toHaveProperty('top');
      expect(insets).toHaveProperty('right');
      expect(insets).toHaveProperty('bottom');
      expect(insets).toHaveProperty('left');
    });
  });

  describe('Install Prompt', () => {
    it('should check if install prompt is available', () => {
      const isAvailable = service.isInstallPromptAvailable();
      expect(typeof isAvailable).toBe('boolean');
    });

    it('should provide installPrompt$ observable', (done) => {
      service.installPrompt$.subscribe(prompt => {
        expect(prompt === null || prompt instanceof Event).toBe(true);
        done();
      });
    });
  });

  describe('Haptic Feedback', () => {
    it('should trigger haptic feedback', () => {
      expect(() => {
        service.triggerHapticFeedback('medium');
      }).not.toThrow();
    });
  });

  describe('Storage', () => {
    it('should get storage info', async () => {
      const storage = await service.getStorageInfo();
      expect(storage).toHaveProperty('usage');
      expect(storage).toHaveProperty('quota');
    });
  });
});

