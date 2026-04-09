import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VendorFooterNav } from './vendor-footer-nav';

describe('VendorFooterNav', () => {
  let component: VendorFooterNav;
  let fixture: ComponentFixture<VendorFooterNav>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VendorFooterNav]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VendorFooterNav);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
