import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WorkerProfile } from './worker-profile';

describe('WorkerProfile', () => {
  let component: WorkerProfile;
  let fixture: ComponentFixture<WorkerProfile>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WorkerProfile]
    })
    .compileComponents();

    fixture = TestBed.createComponent(WorkerProfile);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
