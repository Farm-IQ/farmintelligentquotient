import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LenderInsights } from './lender-insights';

describe('LenderInsights', () => {
  let component: LenderInsights;
  let fixture: ComponentFixture<LenderInsights>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LenderInsights]
    })
    .compileComponents();

    fixture = TestBed.createComponent(LenderInsights);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
