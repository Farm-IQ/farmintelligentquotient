import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AdminModelOperations } from './admin-model-operations';

describe('AdminModelOperations', () => {
  let component: AdminModelOperations;
  let fixture: ComponentFixture<AdminModelOperations>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdminModelOperations]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AdminModelOperations);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
