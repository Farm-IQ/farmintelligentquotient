import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WorkerAttendanceTracker } from './worker-attendance-tracker';

describe('WorkerAttendanceTracker', () => {
  let component: WorkerAttendanceTracker;
  let fixture: ComponentFixture<WorkerAttendanceTracker>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WorkerAttendanceTracker]
    })
    .compileComponents();

    fixture = TestBed.createComponent(WorkerAttendanceTracker);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
