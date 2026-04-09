import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CooperativeNavbar } from './cooperative-navbar';

describe('CooperativeNavbar', () => {
  let component: CooperativeNavbar;
  let fixture: ComponentFixture<CooperativeNavbar>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CooperativeNavbar]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CooperativeNavbar);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
