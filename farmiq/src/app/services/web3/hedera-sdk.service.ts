/**
 * Hedera SDK Service (Frontend)
 * Uses Hedera JavaScript SDK for client-side wallet operations
 * Handles token queries, balance checks, and transaction execution
 * 
 * NOTE: This is a CLIENT-SIDE service. The backend uses Mirror Node REST API.
 */

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import {
  Client,
  AccountId,
  TokenId,
  Hbar,
  AccountBalanceQuery,
  TokenInfoQuery,
  TokenAssociateTransaction,
  TransferTransaction,
  AccountInfoQuery,
  LedgerId
} from '@hashgraph/sdk';
import { environment } from '../../../environments/environment';

export interface HederaAccount {
  accountId: string;
  balance: Hbar;
  network: 'testnet' | 'mainnet' | 'previewnet';
}

export interface TokenInfo {
  tokenId: string;
  name: string;
  symbol: string;
  decimals: number;
  totalSupply: number;
}

export interface AccountTokenBalance {
  tokenId: string;
  balance: number;
  decimals: number;
}

@Injectable({ providedIn: 'root' })
export class HederaSdkService {
  private client: Client | null = null;
  private readonly NETWORK: 'testnet' | 'mainnet' | 'previewnet' = 'testnet';
  private readonly FIQ_TOKEN_ID = '0.0.8509491'; // FIQ Token ID on Hedera

  constructor(private http: HttpClient) {
    this.initializeHederaClient();
  }

  /**
   * Initialize Hedera client for the configured network
   */
  private initializeHederaClient(): void {
    try {
      // Create a client for the specified network
      // This client is READ-ONLY for public queries
      if (this.NETWORK === 'mainnet') {
        this.client = Client.forMainnet();
      } else if (this.NETWORK === 'previewnet') {
        this.client = Client.forPreviewnet();
      } else {
        this.client = Client.forTestnet();
      }

      console.log(`✓ Hedera SDK initialized for ${this.NETWORK}`);
    } catch (error) {
      console.error('Failed to initialize Hedera SDK:', error);
    }
  }

  /**
   * Query account balance using Hedera SDK
   * This requires the account to have signed in with HashPack
   */
  async getAccountBalance(accountId: string): Promise<Hbar | null> {
    try {
      if (!this.client) return null;

      const account = AccountId.fromString(accountId);
      const balance = await new AccountBalanceQuery()
        .setAccountId(account)
        .execute(this.client);

      console.log(`Account ${accountId} balance: ${balance.hbars} HBAR`);
      return balance.hbars;
    } catch (error) {
      console.error(`Error querying balance for ${accountId}:`, error);
      return null;
    }
  }

  /**
   * Get account information
   */
  async getAccountInfo(accountId: string): Promise<any> {
    try {
      if (!this.client) return null;

      const account = AccountId.fromString(accountId);
      const info = await new AccountInfoQuery()
        .setAccountId(account)
        .execute(this.client);

      console.log(`Account info for ${accountId}:`, info);
      return info;
    } catch (error) {
      console.error(`Error querying account info for ${accountId}:`, error);
      return null;
    }
  }

  /**
   * Get token information
   */
  async getTokenInfo(tokenIdString: string): Promise<TokenInfo | null> {
    try {
      if (!this.client) return null;

      const tokenId = TokenId.fromString(tokenIdString);
      const info = await new TokenInfoQuery()
        .setTokenId(tokenId)
        .execute(this.client);

      return {
        tokenId: info.tokenId.toString(),
        name: info.name,
        symbol: info.symbol,
        decimals: info.decimals,
        totalSupply: info.totalSupply.toNumber()
      };
    } catch (error) {
      console.error(`Error querying token info for ${tokenIdString}:`, error);
      return null;
    }
  }

  /**
   * Get FIQ token info
   */
  async getFiqTokenInfo(): Promise<TokenInfo | null> {
    return this.getTokenInfo(this.FIQ_TOKEN_ID);
  }

  /**
   * Query account's token balances using Hedera Mirror Node REST API
   * (Client-side query to public endpoint)
   */
  async getAccountTokenBalances(accountId: string): Promise<AccountTokenBalance[]> {
    try {
      const mirrorNodeUrl = this.getMirrorNodeUrl();
      const url = `${mirrorNodeUrl}/accounts/${accountId}/tokens`;

      const response = await this.http.get<any>(url).toPromise();

      if (response?.tokens) {
        return response.tokens.map((token: any) => ({
          tokenId: token.token_id,
          balance: parseInt(token.balance),
          decimals: token.decimals || 0
        }));
      }

      return [];
    } catch (error) {
      console.error(`Error querying token balances for ${accountId}:`, error);
      return [];
    }
  }

  /**
   * Get specific token balance for an account
   */
  async getTokenBalance(accountId: string, tokenId: string): Promise<number | null> {
    try {
      const balances = await this.getAccountTokenBalances(accountId);
      const balance = balances.find(b => b.tokenId === tokenId);
      return balance ? balance.balance : null;
    } catch (error) {
      console.error(`Error querying token balance:`, error);
      return null;
    }
  }

  /**
   * Get FIQ token balance for an account
   */
  async getFiqBalance(accountId: string): Promise<number | null> {
    return this.getTokenBalance(accountId, this.FIQ_TOKEN_ID);
  }

  /**
   * Get Mirror Node URL based on current network
   */
  private getMirrorNodeUrl(): string {
    switch (this.NETWORK) {
      case 'mainnet':
        return 'https://mainnet-public.mirrornode.hedera.com/api/v1';
      case 'previewnet':
        return 'https://previewnet.mirrornode.hedera.com/api/v1';
      case 'testnet':
      default:
        return 'https://testnet.mirrornode.hedera.com/api/v1';
    }
  }

  /**
   * Get Hedera account ID from HashPack wallet
   * This is called after wallet connection
   */
  async getHashPackAccountId(): Promise<string | null> {
    try {
      if (typeof window === 'undefined') return null;

      const hashconnect = (window as any).hashconnect;
      if (!hashconnect) {
        console.warn('HashConnect not available');
        return null;
      }

      const data = await hashconnect.getAccountInfo();
      return data?.account || null;
    } catch (error) {
      console.error('Error getting HashPack account:', error);
      return null;
    }
  }

  /**
   * Verify if account is on correct Hedera network
   */
  async verifyHederaNetwork(accountId: string): Promise<boolean> {
    try {
      const info = await this.getAccountInfo(accountId);
      return !!info;
    } catch (error) {
      console.error('Error verifying Hedera network:', error);
      return false;
    }
  }
}
