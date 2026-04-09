import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WorkerPerformanceTracker } from './worker-performance-tracker';

describe('WorkerPerformanceTracker', () => {
  let component: WorkerPerformanceTracker;
  let fixture: ComponentFixture<WorkerPerformanceTracker>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WorkerPerformanceTracker]
    })
    .compileComponents();

    fixture = TestBed.createComponent(WorkerPerformanceTracker);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
