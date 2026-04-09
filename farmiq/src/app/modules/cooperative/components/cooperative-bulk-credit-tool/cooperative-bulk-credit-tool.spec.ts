import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CooperativeBulkCreditTool } from './cooperative-bulk-credit-tool';

describe('CooperativeBulkCreditTool', () => {
  let component: CooperativeBulkCreditTool;
  let fixture: ComponentFixture<CooperativeBulkCreditTool>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CooperativeBulkCreditTool]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CooperativeBulkCreditTool);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
