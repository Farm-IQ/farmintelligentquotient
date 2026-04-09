import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LenderLoanDecision } from './lender-loan-decision';

describe('LenderLoanDecision', () => {
  let component: LenderLoanDecision;
  let fixture: ComponentFixture<LenderLoanDecision>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LenderLoanDecision]
    })
    .compileComponents();

    fixture = TestBed.createComponent(LenderLoanDecision);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
