import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WorkerTaskManager } from './worker-task-manager';

describe('WorkerTaskManager', () => {
  let component: WorkerTaskManager;
  let fixture: ComponentFixture<WorkerTaskManager>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WorkerTaskManager]
    })
    .compileComponents();

    fixture = TestBed.createComponent(WorkerTaskManager);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
