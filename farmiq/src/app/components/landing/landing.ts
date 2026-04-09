import { Component, OnInit, OnDestroy, Inject, PLATFORM_ID, NgZone } from '@angular/core';
import { CommonModule, NgOptimizedImage, isPlatformBrowser } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { SupabaseService } from '../../services/core/supabase.service';

@Component({
  selector: 'app-landing',
  imports: [CommonModule, RouterLink, NgOptimizedImage, FormsModule],
  templateUrl: './landing.html',
  styleUrl: './landing.scss',
})
export class LandingComponent implements OnInit, OnDestroy {
  customAmount: number | null = null;
  customTokens: number = 0;
  showMobileMenu = false;
  showFeatureModal = false;
  selectedFeature: any = null;
  private isBrowser = false;
  private lastScrollY = 0;
  
  readonly TOKEN_PRICE = 1; // 1 FQ = 1 KSH
  readonly BONUS_PERCENTAGE = 0.10; // 10% bonus
  totalKshPrice = 0; // Total KSH price

  tokenPackages = [
    { tokens: 50, featured: false },
    { tokens: 150, featured: false },
    { tokens: 500, featured: true },
    { tokens: 1000, featured: false }
  ];

  constructor(
    @Inject(PLATFORM_ID) private platformId: Object,
    private ngZone: NgZone,
    private supabaseService: SupabaseService
  ) {
    this.isBrowser = isPlatformBrowser(this.platformId);
  }
  features = [
    {
      title: 'Credit Scoring',
      description: 'Get instant credit scores powered by AI and blockchain technology',
      detailedDescription: 'Our AI-powered credit scoring system instantly evaluates your farming profile, transaction history, and collateral using blockchain verification. Get approved for credit lines in minutes instead of months. Your FarmIQ score unlocks access to loans, input financing, and supplier credit.',
      icon: '💳',
      color: '#667eea'
    },
    {
      title: 'Farm Analytics',
      description: 'Real-time farm metrics and performance analytics for better decision making',
      detailedDescription: 'Monitor your farm performance in real-time with comprehensive dashboards. Track yield metrics, soil health, water usage, and crop progress. Get actionable insights to optimize farming practices and increase productivity by up to 40%.',
      icon: '📊',
      color: '#f093fb'
    },
    {
      title: 'Market Intelligence',
      description: 'Real-time commodity prices and agricultural market insights',
      detailedDescription: 'Access live commodity prices, market trends, and demand forecasts. Make informed decisions about when to sell your produce at peak prices. Compare prices across markets and negotiate better deals.',
      icon: '📈',
      color: '#4facfe'
    },
    {
      title: 'Agronomy AI',
      description: 'AI-powered chatbot for crop health monitoring and farming advice',
      detailedDescription: 'Get expert farming advice from our AI chatbot trained on agricultural best practices. Get answers to crop health questions, pest management strategies, and seasonal planting schedules. Available 24/7 in your local language.',
      icon: '🤖',
      color: '#43e97b'
    },
    {
      title: 'Wallet Integration',
      description: 'Connect MetaMask, HashPack, and manage blockchain transactions',
      detailedDescription: 'Securely connect your crypto wallets and manage blockchain transactions. Store FQ tokens, participate in decentralized protocols, and access tokenized credit lines. Full support for Hedera and Ethereum networks.',
      icon: '💰',
      color: '#fa709a'
    },
    {
      title: 'USSD Support',
      description: 'Access FarmIQ services via USSD on basic mobile phones',
      detailedDescription: 'Don\'t have a smartphone? No problem. Use USSD codes to access core FarmIQ features on any mobile phone. Check crop alerts, market prices, and manage your account via SMS. Works offline in low-connectivity areas.',
      icon: '📱',
      color: '#fee140'
    }
  ];

  testimonials = [
    {
      name: 'John Kipchoge',
      role: 'Corn Farmer, Kenya',
      message: 'FarmIQ helped me increase my crop yield by 40% with data-driven insights',
      avatar: '👨‍🌾'
    },
    {
      name: 'Mary Odhiambo',
      role: 'Dairy Farmer, Uganda',
      message: 'The credit scoring system helped me secure a loan in minutes, not weeks',
      avatar: '👩‍🌾'
    },
    {
      name: 'Ahmed Hassan',
      role: 'Agribusiness Owner, Tanzania',
      message: 'Blockchain integration gave me confidence in transparent transactions',
      avatar: '👨‍💼'
    }
  ];

  scrollToSection(section: string): void {
    if (!this.isBrowser) return;
    
    // Close menu first
    this.showMobileMenu = false;
    
    const element = document.getElementById(section);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  }

  closeMenu(): void {
    this.showMobileMenu = false;
  }

  navigateHome(): void {
    if (!this.isBrowser) return;
    
    // Already at home, just scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  contactSales(): void {
    if (!this.isBrowser) return;
    
    // Open contact form or email
    const subject = encodeURIComponent('Enterprise Plan Inquiry');
    const body = encodeURIComponent('Hi,\n\nI am interested in the Enterprise plan for FarmIQ. Please provide more information.\n\nThank you');
    window.location.href = `mailto:sales@farmiq.com?subject=${subject}&body=${body}`;
  }

  getPackagePrice(tokens: number): number {
    return tokens * this.TOKEN_PRICE;
  }

  getPackageBonus(tokens: number): number {
    return Math.floor(tokens * this.BONUS_PERCENTAGE);
  }

  getPackageTotalTokens(tokens: number): number {
    return tokens + this.getPackageBonus(tokens);
  }

  calculateTokens(): void {
    if (this.customAmount && this.customAmount > 0) {
      const baseTokens = this.customAmount / this.TOKEN_PRICE;
      const bonus = baseTokens * this.BONUS_PERCENTAGE;
      this.customTokens = parseFloat((baseTokens + bonus).toFixed(2));
      this.totalKshPrice = this.customAmount;
    } else {
      this.customTokens = 0;
      this.totalKshPrice = 0;
    }
  }

  buyTokens(amount: number): void {
    if (!this.isBrowser) return;
    
    console.log(`Opening checkout for ${amount} FQ tokens`);
    
    // Check if user is authenticated
    const currentUser = this.supabaseService.userSignal$();
    if (!currentUser) {
      // Redirect to login
      console.log('User not authenticated, redirecting to login');
      window.location.href = '/login';
      return;
    }

    // Navigate to checkout with token amount as query param
    const checkoutUrl = `/checkout?tokens=${amount}&price=${amount * this.TOKEN_PRICE}`;
    console.log('Navigating to:', checkoutUrl);
    window.location.href = checkoutUrl;
  }

  openFeatureModal(feature: any): void {
    this.selectedFeature = feature;
    this.showFeatureModal = true;
    
    if (this.isBrowser) {
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden';
    }
  }

  closeFeatureModal(): void {
    this.showFeatureModal = false;
    this.selectedFeature = null;
    
    if (this.isBrowser) {
      // Re-enable body scroll
      document.body.style.overflow = '';
    }
  }

  /**
   * Show success message after payment
   */
  private showSuccessMessage(tokens: number): void {
    // Success notification
    alert(`✓ Success! ${tokens} FQ tokens have been added to your account.`);
  }

  onImageLoad(event: Event): void {
    const img = event.target as HTMLImageElement;
    console.log('Logo image loaded successfully:', img.src);
    img.style.opacity = '1';
  }

  onImageError(event: Event): void {
    const img = event.target as HTMLImageElement;
    console.error('Failed to load logo image from:', img.src);
    // Fallback: try alternate path
    if (!img.src.includes('fallback')) {
      img.src = '/logo.png';
      img.style.opacity = '0.5';
    }
  }

  ngOnInit(): void {
    // Any initialization logic
  }

  toggleMobileMenu(): void {
    this.showMobileMenu = !this.showMobileMenu;
    
    if (!this.isBrowser) return;

    try {
      // Allow background scrolling - removed overflow: hidden
      
      // Focus management for accessibility
      if (this.showMobileMenu) {
        // Move focus to mobile menu close button when opening
        setTimeout(() => {
          const closeBtn = document.querySelector('.mobile-menu-close') as HTMLButtonElement;
          if (closeBtn) {
            closeBtn.focus();
          }
        }, 100);
      } else {
        // Return focus to hamburger menu when closing
        const hamburger = document.querySelector('.navbar-toggle') as HTMLButtonElement;
        if (hamburger) {
          hamburger.focus();
        }
      }
    } catch (e) {
      // ignore
    }
  }

  private handleKeydown = (ev: KeyboardEvent) => {
    if (ev.key === 'Escape') {
      if (this.showFeatureModal) {
        this.closeFeatureModal();
      } else if (this.showMobileMenu) {
        this.toggleMobileMenu();
      }
    }
  }

  private handleScroll = () => {
    if (!this.isBrowser) return;
    
    const currentScrollY = window.scrollY;
    
    // Close menu if user scrolls down or up
    if (this.showMobileMenu && Math.abs(currentScrollY - this.lastScrollY) > 5) {
      this.ngZone.run(() => {
        this.showMobileMenu = false;
      });
    }
    
    this.lastScrollY = currentScrollY;
  }

  ngAfterViewInit(): void {
    if (!this.isBrowser) return;
    
    document.addEventListener('keydown', this.handleKeydown);
    
    // Use ngZone to run scroll listener outside Angular zone for better performance
    this.ngZone.runOutsideAngular(() => {
      window.addEventListener('scroll', this.handleScroll, { passive: true });
    });
  }

  ngOnDestroy(): void {
    if (!this.isBrowser) return;
    
    try {
      document.body.style.overflow = '';
    } catch (e) {
      // ignore
    }
    document.removeEventListener('keydown', this.handleKeydown);
    window.removeEventListener('scroll', this.handleScroll);
    
    // Clean up feature modal
    if (this.showFeatureModal) {
      this.closeFeatureModal();
    }
  }
}
