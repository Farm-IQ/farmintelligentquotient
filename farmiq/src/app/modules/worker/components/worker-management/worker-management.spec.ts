import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WorkerManagement } from './worker-management';

describe('WorkerManagement', () => {
  let component: WorkerManagement;
  let fixture: ComponentFixture<WorkerManagement>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WorkerManagement]
    })
    .compileComponents();

    fixture = TestBed.createComponent(WorkerManagement);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
