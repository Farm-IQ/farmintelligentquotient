import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LenderWallet } from './lender-wallet';

describe('LenderWallet', () => {
  let component: LenderWallet;
  let fixture: ComponentFixture<LenderWallet>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LenderWallet]
    })
    .compileComponents();

    fixture = TestBed.createComponent(LenderWallet);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
