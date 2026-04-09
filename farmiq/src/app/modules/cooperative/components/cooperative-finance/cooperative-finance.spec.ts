import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CooperativeFinance } from './cooperative-finance';

describe('CooperativeFinance', () => {
  let component: CooperativeFinance;
  let fixture: ComponentFixture<CooperativeFinance>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CooperativeFinance]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CooperativeFinance);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
