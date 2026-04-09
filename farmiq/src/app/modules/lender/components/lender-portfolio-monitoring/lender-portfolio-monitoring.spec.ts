import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LenderPortfolioMonitoring } from './lender-portfolio-monitoring';

describe('LenderPortfolioMonitoring', () => {
  let component: LenderPortfolioMonitoring;
  let fixture: ComponentFixture<LenderPortfolioMonitoring>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LenderPortfolioMonitoring]
    })
    .compileComponents();

    fixture = TestBed.createComponent(LenderPortfolioMonitoring);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
