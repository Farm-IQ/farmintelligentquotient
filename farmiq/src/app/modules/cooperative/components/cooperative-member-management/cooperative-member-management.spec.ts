import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CooperativeMemberManagement } from './cooperative-member-management';

describe('CooperativeMemberManagement', () => {
  let component: CooperativeMemberManagement;
  let fixture: ComponentFixture<CooperativeMemberManagement>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CooperativeMemberManagement]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CooperativeMemberManagement);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
