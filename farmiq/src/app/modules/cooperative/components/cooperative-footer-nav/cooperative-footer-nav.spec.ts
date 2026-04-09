import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CooperativeFooterNav } from './cooperative-footer-nav';

describe('CooperativeFooterNav', () => {
  let component: CooperativeFooterNav;
  let fixture: ComponentFixture<CooperativeFooterNav>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CooperativeFooterNav]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CooperativeFooterNav);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
