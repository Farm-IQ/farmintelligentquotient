import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { VendorModuleRoutingModule } from './vendor-module-routing-module';
import { VendorDashboard } from './components/vendor-dashboard/vendor-dashboard';
import { VendorProfile } from './components/vendor-profile/vendor-profile';
import { VendorProductCatalog } from './components/vendor-product-catalog/vendor-product-catalog';
import { VendorOrders } from './components/vendor-orders/vendor-orders';
import { VendorAnalytics } from './components/vendor-analytics/vendor-analytics';
import { VendorWallet } from './components/vendor-wallet/vendor-wallet';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    VendorModuleRoutingModule,
    VendorDashboard,
    VendorProfile,
    VendorProductCatalog,
    VendorOrders,
    VendorAnalytics,
    VendorWallet
  ]
})
export class VendorModuleModule { }
