import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AgentFooterNav } from './agent-footer-nav';

describe('AgentFooterNav', () => {
  let component: AgentFooterNav;
  let fixture: ComponentFixture<AgentFooterNav>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AgentFooterNav]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AgentFooterNav);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
