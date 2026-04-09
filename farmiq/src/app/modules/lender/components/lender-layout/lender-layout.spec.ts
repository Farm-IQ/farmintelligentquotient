import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LenderLayout } from './lender-layout';

describe('LenderLayout', () => {
  let component: LenderLayout;
  let fixture: ComponentFixture<LenderLayout>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LenderLayout]
    })
    .compileComponents();

    fixture = TestBed.createComponent(LenderLayout);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
