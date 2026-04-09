import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WorkerNavbar } from './worker-navbar';

describe('WorkerNavbar', () => {
  let component: WorkerNavbar;
  let fixture: ComponentFixture<WorkerNavbar>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WorkerNavbar]
    })
    .compileComponents();

    fixture = TestBed.createComponent(WorkerNavbar);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
