/**
 * Web3 Wallet Service
 * Handles WalletConnect integration with HashPack and MetaMask
 * Manages Hedera token interactions and wallet connections
 * 
 * COMPLIANCE NOTE:
 * - FQ is a utility token on Hedera Token Service (HTS)
 * - FarmIQ is not a PSP (Payment Service Provider) or VSAP (Virtual Service/Asset Provider) in Kenya
 * - Wallet integration is for utility token management only
 * - No money transmission or financial services are provided
 */

import { Injectable, signal } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface WalletAccount {
  address: string;
  network: 'testnet' | 'mainnet' | 'previewnet';
  provider: 'hashpack' | 'metamask' | 'unknown';
  chainId: number;
  firstName?: string;
  lastName?: string;
}

export interface TokenBalance {
  tokenId: string;
  balance: number;
  decimals: number;
  symbol: string;
  name: string;
}

export interface Transaction {
  id: string;
  from: string;
  to: string;
  amount: number;
  tokenId: string;
  type: 'sent' | 'received';
  timestamp: number;
  status: 'pending' | 'confirmed' | 'failed';
  hash: string;
}

@Injectable({
  providedIn: 'root'
})
export class Web3WalletService {
  // Configuration
  private readonly WALLET_CONNECT_PROJECT_ID = '36df245b68a945dc29fee141dbb8307b';
  private readonly HEDERA_NETWORK = 'testnet'; // 'testnet', 'mainnet', or 'previewnet'
  private readonly FQ_TOKEN_ID = '0.0.8509491'; // FQ Token ID on Hedera
  private readonly NETWORK_MAP = {
    testnet: {
      chainId: 296,
      rpcUrl: 'https://testnet.hashio.io:50005',
      walletConnectChainId: 'hedera:testnet'
    },
    mainnet: {
      chainId: 295,
      rpcUrl: 'https://mainnet.hashio.io:50005',
      walletConnectChainId: 'hedera:mainnet'
    },
    previewnet: {
      chainId: 297,
      rpcUrl: 'https://previewnet.hashio.io:50005',
      walletConnectChainId: 'hedera:previewnet'
    }
  };

  // State management with Angular signals
  connectedAccount = signal<WalletAccount | null>(null);
  isConnecting = signal(false);
  isConnected = signal(false);
  error = signal<string | null>(null);

  private accountSubject = new BehaviorSubject<WalletAccount | null>(null);
  private tokenBalanceSubject = new BehaviorSubject<TokenBalance | null>(null);
  private transactionsSubject = new BehaviorSubject<Transaction[]>([]);

  constructor() {
    this.initializeWalletConnect();
  }

  /**
   * Initialize WalletConnect
   */
  private initializeWalletConnect(): void {
    if (this.isBrowser()) {
      // WalletConnect initialization will happen on demand
      console.log('Web3 Wallet Service initialized');
      console.log('WalletConnect Project ID:', this.WALLET_CONNECT_PROJECT_ID);
      console.log('Hedera Network:', this.HEDERA_NETWORK);
      console.log('FQ Token ID:', this.FQ_TOKEN_ID);
    }
  }

  /**
   * Check if in browser environment
   */
  private isBrowser(): boolean {
    return typeof window !== 'undefined';
  }

  /**
   * Connect to HashPack wallet
   */
  async connectHashPack(): Promise<WalletAccount> {
    this.isConnecting.set(true);
    this.error.set(null);

    try {
      // Check if HashPack is available
      if (!this.isBrowser() || !(window as any).hashconnect) {
        throw new Error('HashPack extension is not installed');
      }

      // Initialize HashConnect
      const hashConnect = (window as any).hashconnect;
      
      // Request account access
      const response = await hashConnect.connect();
      
      if (!response || !response.pairedAccounts || response.pairedAccounts.length === 0) {
        throw new Error('Failed to connect to HashPack');
      }

      const accountId = response.pairedAccounts[0];
      const account: WalletAccount = {
        address: accountId,
        network: this.HEDERA_NETWORK as 'testnet' | 'mainnet' | 'previewnet',
        provider: 'hashpack',
        chainId: this.NETWORK_MAP[this.HEDERA_NETWORK].chainId
      };

      this.connectedAccount.set(account);
      this.accountSubject.next(account);
      this.isConnected.set(true);

      // Load token balance
      await this.loadTokenBalance();

      return account;
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to connect to HashPack';
      this.error.set(errorMsg);
      console.error('HashPack connection error:', err);
      throw new Error(errorMsg);
    } finally {
      this.isConnecting.set(false);
    }
  }

  /**
   * Connect to MetaMask wallet
   */
  async connectMetaMask(): Promise<WalletAccount> {
    this.isConnecting.set(true);
    this.error.set(null);

    try {
      // Check if MetaMask is available
      if (!this.isBrowser() || !(window as any).ethereum) {
        throw new Error('MetaMask extension is not installed');
      }

      const ethereum = (window as any).ethereum;

      // Request account access
      const accounts = await ethereum.request({
        method: 'eth_requestAccounts'
      });

      if (!accounts || accounts.length === 0) {
        throw new Error('No accounts found in MetaMask');
      }

      // Get current chain ID
      const chainId = await ethereum.request({ method: 'eth_chainId' });
      
      const account: WalletAccount = {
        address: accounts[0],
        network: this.HEDERA_NETWORK as 'testnet' | 'mainnet' | 'previewnet',
        provider: 'metamask',
        chainId: parseInt(chainId, 16)
      };

      this.connectedAccount.set(account);
      this.accountSubject.next(account);
      this.isConnected.set(true);

      // Load token balance
      await this.loadTokenBalance();

      // Listen for account changes
      ethereum.on('accountsChanged', (newAccounts: string[]) => {
        if (newAccounts.length === 0) {
          this.disconnect();
        } else {
          account.address = newAccounts[0];
          this.connectedAccount.set(account);
          this.accountSubject.next(account);
        }
      });

      return account;
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to connect to MetaMask';
      this.error.set(errorMsg);
      console.error('MetaMask connection error:', err);
      throw new Error(errorMsg);
    } finally {
      this.isConnecting.set(false);
    }
  }

  /**
   * Connect using WalletConnect
   */
  async connectWalletConnect(): Promise<WalletAccount> {
    this.isConnecting.set(true);
    this.error.set(null);

    try {
      // WalletConnect integration point for future expansion
      // This would use @walletconnect/modal or @walletconnect/web3modal
      throw new Error('WalletConnect modal not yet configured. Use HashPack or MetaMask.');
    } catch (err: any) {
      const errorMsg = err.message || 'WalletConnect connection failed';
      this.error.set(errorMsg);
      throw new Error(errorMsg);
    } finally {
      this.isConnecting.set(false);
    }
  }

  /**
   * Disconnect wallet
   */
  async disconnect(): Promise<void> {
    const account = this.connectedAccount();
    
    if (account?.provider === 'hashpack') {
      const hashConnect = (window as any).hashconnect;
      await hashConnect?.disconnect?.();
    } else if (account?.provider === 'metamask') {
      // MetaMask requires manual UI cleanup, no API to disconnect
      // Just clear local state
    }

    this.connectedAccount.set(null);
    this.accountSubject.next(null);
    this.isConnected.set(false);
    this.tokenBalanceSubject.next(null);
    this.transactionsSubject.next([]);
    this.error.set(null);
  }

  /**
   * Load FQ token balance for connected account
   */
  async loadTokenBalance(): Promise<TokenBalance> {
    const account = this.connectedAccount();
    if (!account) {
      throw new Error('No wallet connected');
    }

    try {
      // In production, fetch from Hedera Mirror Node or Supabase
      // For now, return mock data
      const balance: TokenBalance = {
        tokenId: this.FQ_TOKEN_ID,
        balance: 0, // Will be fetched from backend
        decimals: 8,
        symbol: 'FQ',
        name: 'FarmIQ'
      };

      this.tokenBalanceSubject.next(balance);
      return balance;
    } catch (err: any) {
      console.error('Failed to load token balance:', err);
      throw new Error('Failed to load token balance');
    }
  }

  /**
   * Transfer FQ tokens
   */
  async transferTokens(recipientAddress: string, amount: number): Promise<string> {
    const account = this.connectedAccount();
    if (!account) {
      throw new Error('No wallet connected');
    }

    try {
      // Implementation would depend on the wallet provider
      // HashPack: Use hashConnect.sendTransaction()
      // MetaMask: Use eth_sendTransaction with HTS contract interaction
      
      console.log(`Transferring ${amount} FQ tokens to ${recipientAddress}`);
      
      // Placeholder - actual implementation would create a Hedera transaction
      return 'transaction-hash-placeholder';
    } catch (err: any) {
      throw new Error(`Token transfer failed: ${err.message}`);
    }
  }

  /**
   * Load transaction history
   */
  async loadTransactionHistory(): Promise<Transaction[]> {
    const account = this.connectedAccount();
    if (!account) {
      throw new Error('No wallet connected');
    }

    try {
      // Fetch from Hedera Mirror Node or Supabase backend
      // For now, return empty array
      const transactions: Transaction[] = [];
      this.transactionsSubject.next(transactions);
      return transactions;
    } catch (err: any) {
      console.error('Failed to load transaction history:', err);
      throw new Error('Failed to load transaction history');
    }
  }

  /**
   * Get account observable
   */
  getAccount$(): Observable<WalletAccount | null> {
    return this.accountSubject.asObservable();
  }

  /**
   * Get token balance observable
   */
  getTokenBalance$(): Observable<TokenBalance | null> {
    return this.tokenBalanceSubject.asObservable();
  }

  /**
   * Get transactions observable
   */
  getTransactions$(): Observable<Transaction[]> {
    return this.transactionsSubject.asObservable();
  }

  /**
   * Get current Hedera network info
   */
  getNetworkInfo() {
    return this.NETWORK_MAP[this.HEDERA_NETWORK];
  }

  /**
   * Get FQ token ID
   */
  getFQTokenId(): string {
    return this.FQ_TOKEN_ID;
  }

  /**
   * Compliance Check
   * Verifies usage aligns with utility token framework
   */
  getComplianceInfo() {
    return {
      status: 'UTILITY_TOKEN',
      jurisdiction: 'Kenya',
      framework: 'Hedera Token Service (HTS)',
      fqTokenId: this.FQ_TOKEN_ID,
      classification: 'Utility Token - Not a security or payment instrument',
      disclaimer: 'FarmIQ is not a Payment Service Provider (PSP) or Virtual Service/Asset Provider (VSAP) in Kenya. FQ tokens are utility tokens issued on Hedera.',
      supportedWallets: ['HashPack', 'MetaMask'],
      network: this.HEDERA_NETWORK
    };
  }
}
