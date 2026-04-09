import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AgentLayout } from './agent-layout';

describe('AgentLayout', () => {
  let component: AgentLayout;
  let fixture: ComponentFixture<AgentLayout>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AgentLayout]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AgentLayout);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
