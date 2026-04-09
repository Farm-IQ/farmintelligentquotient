import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VendorNavbar } from './vendor-navbar';

describe('VendorNavbar', () => {
  let component: VendorNavbar;
  let fixture: ComponentFixture<VendorNavbar>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VendorNavbar]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VendorNavbar);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
