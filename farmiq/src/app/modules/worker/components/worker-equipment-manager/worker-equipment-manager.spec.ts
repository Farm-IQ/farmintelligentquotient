import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WorkerEquipmentManager } from './worker-equipment-manager';

describe('WorkerEquipmentManager', () => {
  let component: WorkerEquipmentManager;
  let fixture: ComponentFixture<WorkerEquipmentManager>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WorkerEquipmentManager]
    })
    .compileComponents();

    fixture = TestBed.createComponent(WorkerEquipmentManager);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
