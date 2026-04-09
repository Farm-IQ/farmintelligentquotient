import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WorkerLayout } from './worker-layout';

describe('WorkerLayout', () => {
  let component: WorkerLayout;
  let fixture: ComponentFixture<WorkerLayout>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WorkerLayout]
    })
    .compileComponents();

    fixture = TestBed.createComponent(WorkerLayout);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
