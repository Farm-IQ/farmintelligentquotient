import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WorkerListView } from './worker-list-view';

describe('WorkerListView', () => {
  let component: WorkerListView;
  let fixture: ComponentFixture<WorkerListView>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WorkerListView]
    })
    .compileComponents();

    fixture = TestBed.createComponent(WorkerListView);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
