import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CooperativeWallet } from './cooperative-wallet';

describe('CooperativeWallet', () => {
  let component: CooperativeWallet;
  let fixture: ComponentFixture<CooperativeWallet>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CooperativeWallet]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CooperativeWallet);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
