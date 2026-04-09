import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FarmerCreditScore } from './farmer-credit-score';

describe('FarmerCreditScore', () => {
  let component: FarmerCreditScore;
  let fixture: ComponentFixture<FarmerCreditScore>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FarmerCreditScore]
    })
    .compileComponents();

    fixture = TestBed.createComponent(FarmerCreditScore);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
