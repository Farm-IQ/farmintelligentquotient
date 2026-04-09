import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AgentOnboarding } from './agent-onboarding';

describe('AgentOnboarding', () => {
  let component: AgentOnboarding;
  let fixture: ComponentFixture<AgentOnboarding>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AgentOnboarding]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AgentOnboarding);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
