import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FarmerAccount } from './farmer-account';

describe('FarmerAccount', () => {
  let component: FarmerAccount;
  let fixture: ComponentFixture<FarmerAccount>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FarmerAccount]
    })
    .compileComponents();

    fixture = TestBed.createComponent(FarmerAccount);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
