import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WorkerPayrollManager } from './worker-payroll-manager';

describe('WorkerPayrollManager', () => {
  let component: WorkerPayrollManager;
  let fixture: ComponentFixture<WorkerPayrollManager>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WorkerPayrollManager]
    })
    .compileComponents();

    fixture = TestBed.createComponent(WorkerPayrollManager);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
