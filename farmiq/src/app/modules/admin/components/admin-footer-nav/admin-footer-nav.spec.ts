import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AdminFooterNav } from './admin-footer-nav';

describe('AdminFooterNav', () => {
  let component: AdminFooterNav;
  let fixture: ComponentFixture<AdminFooterNav>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdminFooterNav]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AdminFooterNav);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
