import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LenderFooterNav } from './lender-footer-nav';

describe('LenderFooterNav', () => {
  let component: LenderFooterNav;
  let fixture: ComponentFixture<LenderFooterNav>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LenderFooterNav]
    })
    .compileComponents();

    fixture = TestBed.createComponent(LenderFooterNav);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
