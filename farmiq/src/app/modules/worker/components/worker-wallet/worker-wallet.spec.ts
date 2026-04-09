import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WorkerWallet } from './worker-wallet';

describe('WorkerWallet', () => {
  let component: WorkerWallet;
  let fixture: ComponentFixture<WorkerWallet>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WorkerWallet]
    })
    .compileComponents();

    fixture = TestBed.createComponent(WorkerWallet);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
