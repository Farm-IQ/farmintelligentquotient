import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CooperativeInsights } from './cooperative-insights';

describe('CooperativeInsights', () => {
  let component: CooperativeInsights;
  let fixture: ComponentFixture<CooperativeInsights>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CooperativeInsights]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CooperativeInsights);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
