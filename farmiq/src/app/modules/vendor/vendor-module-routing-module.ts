import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { VendorLayout } from './components/vendor-layout/vendor-layout';
import { VendorDashboard } from './components/vendor-dashboard/vendor-dashboard';
import { VendorProfile } from './components/vendor-profile/vendor-profile';
import { VendorProductCatalog } from './components/vendor-product-catalog/vendor-product-catalog';
import { VendorOrders } from './components/vendor-orders/vendor-orders';
import { VendorAnalytics } from './components/vendor-analytics/vendor-analytics';
import { VendorWallet } from './components/vendor-wallet/vendor-wallet';

const routes: Routes = [
  {
    path: '',
    component: VendorLayout,
    children: [
      {
        path: '',
        component: VendorDashboard,
        title: 'Vendor Dashboard - FarmIQ'
      },
      {
        path: 'profile',
        component: VendorProfile,
        title: 'Vendor Profile - FarmIQ'
      },
      {
        path: 'products',
        component: VendorProductCatalog,
        title: 'Product Catalog - FarmIQ'
      },
      {
        path: 'orders',
        component: VendorOrders,
        title: 'Orders - FarmIQ'
      },
      {
        path: 'analytics',
        component: VendorAnalytics,
        title: 'Analytics - FarmIQ'
      },
      {
        path: 'wallet',
        component: VendorWallet,
        title: 'Wallet - FarmIQ'
      }
    ]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class VendorModuleRoutingModule { }
