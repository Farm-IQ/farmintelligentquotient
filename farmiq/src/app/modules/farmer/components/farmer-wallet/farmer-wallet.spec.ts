import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FarmerWallet } from './farmer-wallet';

describe('FarmerWallet', () => {
  let component: FarmerWallet;
  let fixture: ComponentFixture<FarmerWallet>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FarmerWallet]
    })
    .compileComponents();

    fixture = TestBed.createComponent(FarmerWallet);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
