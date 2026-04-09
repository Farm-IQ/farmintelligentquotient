import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LenderRiskDashboard } from './lender-risk-dashboard';

describe('LenderRiskDashboard', () => {
  let component: LenderRiskDashboard;
  let fixture: ComponentFixture<LenderRiskDashboard>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LenderRiskDashboard]
    })
    .compileComponents();

    fixture = TestBed.createComponent(LenderRiskDashboard);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
