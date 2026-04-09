import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { IonicModule } from '@ionic/angular';
import { FarmSetupWizardComponent } from './farm-setup-wizard';

describe('FarmSetupWizardComponent', () => {
  let component: FarmSetupWizardComponent;
  let fixture: ComponentFixture<FarmSetupWizardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        FarmSetupWizardComponent,
        ReactiveFormsModule,
        RouterTestingModule,
        IonicModule.forRoot()
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(FarmSetupWizardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('Form Initialization', () => {
    it('should have 4 total steps', () => {
      expect(component.totalSteps).toBe(4);
    });

    it('should start at step 1', () => {
      expect(component.currentStep).toBe(1);
    });

    it('should initialize farm info form', () => {
      expect(component.farmInfoForm).toBeTruthy();
      expect(component.farmInfoForm.get('farmName')).toBeTruthy();
      expect(component.farmInfoForm.get('county')).toBeTruthy();
      expect(component.farmInfoForm.get('farmType')).toBeTruthy();
    });

    it('should initialize parcel form', () => {
      expect(component.parcelForm).toBeTruthy();
      expect(component.parcelForm.get('parcelName')).toBeTruthy();
    });

    it('should initialize worker assignment form', () => {
      expect(component.workerAssignmentForm).toBeTruthy();
      expect(component.workerAssignmentForm.get('selectedWorkers')).toBeTruthy();
    });

    it('should initialize review form', () => {
      expect(component.reviewForm).toBeTruthy();
      expect(component.reviewForm.get('agreedToTerms')).toBeTruthy();
    });
  });

  describe('Step Navigation', () => {
    it('should navigate to next step', () => {
      component.currentStep = 1;
      component.nextStep();
      expect(component.currentStep).toBe(2);
    });

    it('should navigate to previous step', () => {
      component.currentStep = 2;
      component.previousStep();
      expect(component.currentStep).toBe(1);
    });

    it('should not go below step 1', () => {
      component.currentStep = 1;
      component.previousStep();
      expect(component.currentStep).toBe(1);
    });

    it('should not go above total steps', () => {
      component.currentStep = 4;
      component.nextStep();
      expect(component.currentStep).toBe(4);
    });
  });

  describe('Parcel Management', () => {
    it('should add a parcel', () => {
      component.parcelForm.patchValue({
        parcelName: 'Parcel 1',
        parcelType: 'crop_production',
        currentCrop: 'Maize',
        plantingDate: '2024-03-01',
        expectedHarvestDate: '2024-09-01',
        farmingMethod: 'rain_fed',
        irrigationType: 'rain_fed',
        areaHectares: 2.5
      });

      component.addParcel();
      expect(component.parcels.length).toBe(1);
      expect(component.parcels[0].parcelName).toBe('Parcel 1');
    });

    it('should remove a parcel', () => {
      component.parcels = [
        {
          parcelName: 'Parcel 1',
          parcelType: 'crop_production',
          currentCrop: 'Maize',
          plantingDate: '2024-03-01',
          expectedHarvestDate: '2024-09-01',
          farmingMethod: 'rain_fed',
          irrigationType: 'rain_fed',
          areaHectares: 2.5
        }
      ];

      component.removeParcel(0);
      expect(component.parcels.length).toBe(0);
    });
  });

  describe('Worker Selection', () => {
    beforeEach(() => {
      component.availableWorkers = [
        { id: '1', name: 'John Doe', role: 'Farm Manager', phone: '+254712345678' },
        { id: '2', name: 'Jane Smith', role: 'Agronomist', phone: '+254787654321' }
      ];
    });

    it('should toggle worker selection', () => {
      component.toggleWorkerSelection('1');
      expect(component.selectedWorkerIds).toContain('1');

      component.toggleWorkerSelection('1');
      expect(component.selectedWorkerIds).not.toContain('1');
    });

    it('should check if worker is selected', () => {
      component.selectedWorkerIds = ['1'];
      expect(component.isWorkerSelected('1')).toBeTruthy();
      expect(component.isWorkerSelected('2')).toBeFalsy();
    });
  });
});

