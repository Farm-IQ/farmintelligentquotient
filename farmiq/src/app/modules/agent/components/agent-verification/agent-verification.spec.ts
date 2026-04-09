import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AgentVerification } from './agent-verification';

describe('AgentVerification', () => {
  let component: AgentVerification;
  let fixture: ComponentFixture<AgentVerification>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AgentVerification]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AgentVerification);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
