import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CooperativeDashboard } from './cooperative-dashboard';

describe('CooperativeDashboard', () => {
  let component: CooperativeDashboard;
  let fixture: ComponentFixture<CooperativeDashboard>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CooperativeDashboard]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CooperativeDashboard);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
