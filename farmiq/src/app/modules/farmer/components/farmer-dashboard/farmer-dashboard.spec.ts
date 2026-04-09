import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FarmerDashboard } from './farmer-dashboard';

describe('FarmerDashboard', () => {
  let component: FarmerDashboard;
  let fixture: ComponentFixture<FarmerDashboard>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FarmerDashboard]
    })
    .compileComponents();

    fixture = TestBed.createComponent(FarmerDashboard);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
