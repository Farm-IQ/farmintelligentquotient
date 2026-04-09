import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CooperativeLayout } from './cooperative-layout';

describe('CooperativeLayout', () => {
  let component: CooperativeLayout;
  let fixture: ComponentFixture<CooperativeLayout>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CooperativeLayout]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CooperativeLayout);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
