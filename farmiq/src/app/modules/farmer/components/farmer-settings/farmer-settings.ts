import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonicModule } from '@ionic/angular';
import { FarmerService } from '../../services/farmer.service';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-farmer-settings',
  standalone: true,
  imports: [CommonModule, FormsModule, IonicModule],
  templateUrl: './farmer-settings.html',
  styleUrls: ['./farmer-settings.scss']
})
export class FarmerSettingsComponent implements OnInit, OnDestroy {
  settings: any = {
    notifications: true,
    weather_alerts: true,
    farm_size: 0,
    primary_crop: 'maize'
  };
  loading = true;
  saving = false;
  error: string | null = null;
  successMessage: string | null = null;
  private destroy$ = new Subject<void>();

  constructor(private farmerService: FarmerService) {}

  ngOnInit(): void {
    this.loadSettings();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadSettings(): void {
    this.loading = true;
    this.error = null;

    this.farmerService.getSettings()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data: any) => {
          this.settings = data;
          this.loading = false;
        },
        error: (err: any) => {
          this.error = 'Failed to load settings';
          this.loading = false;
        }
      });
  }

  saveSettings(): void {
    this.saving = true;
    this.error = null;
    this.successMessage = null;

    this.farmerService.updateSettings(this.settings)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data: any) => {
          this.saving = false;
          this.successMessage = 'Settings saved successfully!';
          setTimeout(() => {
            this.successMessage = null;
          }, 3000);
        },
        error: (err: any) => {
          this.error = 'Failed to save settings. Please try again.';
          this.saving = false;
        }
      });
  }

  resetSettings(): void {
    this.loadSettings();
  }

  updateSetting(key: string, value: any): void {
    this.settings[key] = value;
  }
}
