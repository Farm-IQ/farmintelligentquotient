import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AdminTokenomics } from './admin-tokenomics';

describe('AdminTokenomics', () => {
  let component: AdminTokenomics;
  let fixture: ComponentFixture<AdminTokenomics>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdminTokenomics]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AdminTokenomics);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
