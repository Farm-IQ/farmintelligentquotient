import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FarmerSettings } from './farmer-settings';

describe('FarmerSettings', () => {
  let component: FarmerSettings;
  let fixture: ComponentFixture<FarmerSettings>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FarmerSettings]
    })
    .compileComponents();

    fixture = TestBed.createComponent(FarmerSettings);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
