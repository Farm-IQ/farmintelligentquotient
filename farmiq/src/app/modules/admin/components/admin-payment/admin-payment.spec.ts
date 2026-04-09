import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AdminPayment } from './admin-payment';

describe('AdminPayment', () => {
  let component: AdminPayment;
  let fixture: ComponentFixture<AdminPayment>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdminPayment]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AdminPayment);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
