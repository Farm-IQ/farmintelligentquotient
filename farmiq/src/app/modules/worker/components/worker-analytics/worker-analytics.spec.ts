import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WorkerAnalytics } from './worker-analytics';

describe('WorkerAnalytics', () => {
  let component: WorkerAnalytics;
  let fixture: ComponentFixture<WorkerAnalytics>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WorkerAnalytics]
    })
    .compileComponents();

    fixture = TestBed.createComponent(WorkerAnalytics);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
