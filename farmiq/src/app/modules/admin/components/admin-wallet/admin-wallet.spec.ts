import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AdminWallet } from './admin-wallet';

describe('AdminWallet', () => {
  let component: AdminWallet;
  let fixture: ComponentFixture<AdminWallet>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdminWallet]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AdminWallet);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
