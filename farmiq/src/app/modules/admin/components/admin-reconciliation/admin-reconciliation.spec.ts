import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AdminReconciliation } from './admin-reconciliation';

describe('AdminReconciliation', () => {
  let component: AdminReconciliation;
  let fixture: ComponentFixture<AdminReconciliation>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdminReconciliation]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AdminReconciliation);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
