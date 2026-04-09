import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VendorLayout } from './vendor-layout';

describe('VendorLayout', () => {
  let component: VendorLayout;
  let fixture: ComponentFixture<VendorLayout>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VendorLayout]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VendorLayout);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
