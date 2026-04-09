import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PwaInstallBanner } from './pwa-install-banner';

describe('PwaInstallBanner', () => {
  let component: PwaInstallBanner;
  let fixture: ComponentFixture<PwaInstallBanner>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PwaInstallBanner]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PwaInstallBanner);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
