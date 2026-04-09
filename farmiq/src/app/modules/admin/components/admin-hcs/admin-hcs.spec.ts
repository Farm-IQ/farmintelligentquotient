import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AdminHcs } from './admin-hcs';

describe('AdminHcs', () => {
  let component: AdminHcs;
  let fixture: ComponentFixture<AdminHcs>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdminHcs]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AdminHcs);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
