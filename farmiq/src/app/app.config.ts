import { ApplicationConfig, provideBrowserGlobalErrorListeners, isDevMode } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors, withFetch } from '@angular/common/http';
import { provideClientHydration, withEventReplay } from '@angular/platform-browser';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { addIcons } from 'ionicons';
import {
  barChartOutline,
  shieldCheckmarkOutline,
  trendingUpOutline,
  walletOutline,
  refreshOutline,
  layersOutline,
  leafOutline,
  earthOutline,
  waterOutline,
  calendarOutline,
  arrowUpOutline,
  closeOutline,
  warningOutline,
  bulbOutline,
  sparklesOutline,
  informationCircleOutline,
  // Add more icons as needed
  menu,
  homeOutline,
  settingsOutline,
  logOutOutline,
  personOutline,
  searchOutline,
  addOutline,
  createOutline,
  trashOutline,
  checkmarkOutline,
  checkmarkCircleOutline,
  arrowDownOutline,
  helpCircleOutline,
  alertCircleOutline,
  statsChartOutline,
  timeOutline,
  documentOutline,
  callOutline,
  mailOutline,
  analyticsOutline,
  chatbubblesOutline,
  notificationsOutline,
  personCircleOutline,
  gridOutline,
  listOutline
} from 'ionicons/icons';

import { routes } from './app.routes';
import { apiInterceptor, errorInterceptor } from './interceptors/core';
import { provideServiceWorker } from '@angular/service-worker';

// Register Ionicons
addIcons({
  'bar-chart-outline': barChartOutline,
  'shield-checkmark-outline': shieldCheckmarkOutline,
  'trending-up-outline': trendingUpOutline,
  'wallet-outline': walletOutline,
  'refresh-outline': refreshOutline,
  'layers-outline': layersOutline,
  'leaf-outline': leafOutline,
  'earth-outline': earthOutline,
  'water-outline': waterOutline,
  'calendar-outline': calendarOutline,
  'arrow-up-outline': arrowUpOutline,
  'close-outline': closeOutline,
  'warning-outline': warningOutline,
  'bulb-outline': bulbOutline,
  'sparkles-outline': sparklesOutline,
  'information-circle-outline': informationCircleOutline,
  // Additional commonly used icons
  menu,
  'home-outline': homeOutline,
  'settings-outline': settingsOutline,
  'log-out-outline': logOutOutline,
  'person-outline': personOutline,
  'search-outline': searchOutline,
  'add-outline': addOutline,
  'create-outline': createOutline,
  'trash-outline': trashOutline,
  'checkmark-outline': checkmarkOutline,
  'checkmark-circle-outline': checkmarkCircleOutline,
  'arrow-down-outline': arrowDownOutline,
  'help-circle-outline': helpCircleOutline,
  'alert-circle-outline': alertCircleOutline,
  'stats-chart-outline': statsChartOutline,
  'time-outline': timeOutline,
  'document-outline': documentOutline,
  'call-outline': callOutline,
  'mail-outline': mailOutline,
  'analytics-outline': analyticsOutline,
  'chatbubbles-outline': chatbubblesOutline,
  'notifications-outline': notificationsOutline,
  'person-circle-outline': personCircleOutline,
  'grid-outline': gridOutline,
  'list-outline': listOutline
});

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideClientHydration(withEventReplay()),
    provideAnimationsAsync(),
    provideHttpClient(
      withFetch(),
      withInterceptors([apiInterceptor, errorInterceptor])
    ),
    provideServiceWorker('ngsw-worker.js', {
      enabled: !isDevMode(),
      registrationStrategy: 'registerWhenStable:30000'
    })
  ]
};
