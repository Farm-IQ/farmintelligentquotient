import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WorkerFooterNav } from './worker-footer-nav';

describe('WorkerFooterNav', () => {
  let component: WorkerFooterNav;
  let fixture: ComponentFixture<WorkerFooterNav>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WorkerFooterNav]
    })
    .compileComponents();

    fixture = TestBed.createComponent(WorkerFooterNav);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
