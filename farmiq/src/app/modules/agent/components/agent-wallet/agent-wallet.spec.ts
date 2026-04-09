import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AgentWallet } from './agent-wallet';

describe('AgentWallet', () => {
  let component: AgentWallet;
  let fixture: ComponentFixture<AgentWallet>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AgentWallet]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AgentWallet);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
