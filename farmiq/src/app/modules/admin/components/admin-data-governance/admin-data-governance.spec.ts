import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AdminDataGovernance } from './admin-data-governance';

describe('AdminDataGovernance', () => {
  let component: AdminDataGovernance;
  let fixture: ComponentFixture<AdminDataGovernance>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdminDataGovernance]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AdminDataGovernance);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
