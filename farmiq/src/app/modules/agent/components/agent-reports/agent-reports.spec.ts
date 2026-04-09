import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AgentReports } from './agent-reports';

describe('AgentReports', () => {
  let component: AgentReports;
  let fixture: ComponentFixture<AgentReports>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AgentReports]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AgentReports);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
