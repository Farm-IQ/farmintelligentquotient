import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FarmerAnalytics } from './farmer-analytics';

describe('FarmerAnalytics', () => {
  let component: FarmerAnalytics;
  let fixture: ComponentFixture<FarmerAnalytics>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FarmerAnalytics]
    })
    .compileComponents();

    fixture = TestBed.createComponent(FarmerAnalytics);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
