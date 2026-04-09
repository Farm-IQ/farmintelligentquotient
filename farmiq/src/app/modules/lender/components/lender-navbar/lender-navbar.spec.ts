import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LenderNavbar } from './lender-navbar';

describe('LenderNavbar', () => {
  let component: LenderNavbar;
  let fixture: ComponentFixture<LenderNavbar>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LenderNavbar]
    })
    .compileComponents();

    fixture = TestBed.createComponent(LenderNavbar);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
