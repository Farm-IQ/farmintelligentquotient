import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AgentNavbar } from './agent-navbar';

describe('AgentNavbar', () => {
  let component: AgentNavbar;
  let fixture: ComponentFixture<AgentNavbar>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AgentNavbar]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AgentNavbar);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
