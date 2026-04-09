/**
 * AUTHENTICATION & CONSTANTS
 * 
 * Authentication constants, enums and utilities
 * Login/Session models are in login.models.ts
 * User profile models are in user-profile.models.ts
 */

// ============================================================================
// KENYA-SPECIFIC CONSTANTS
// ============================================================================

export const KENYAN_COUNTIES = [
  'Nairobi',
  'Mombasa',
  'Kisumu',
  'Nakuru',
  'Uasin Gishu',
  'Kericho',
  'Bomet',
  'Kajiado',
  'Kilifi',
  'Kwale',
  'Lamu',
  'Tana River',
  'Taita Taveta',
  'Machakos',
  'Makueni',
  'Embu',
  'Tharaka Nithi',
  'Kirinyaga',
  'Muranga',
  'Nyeri',
  'Kiambu',
  'Kisii',
  'Nyamira',
  'Trans Nzoia',
  'Elgeyo Marakwet',
  'West Pokot',
  'Samburu',
  'Isiolo',
  'Laikipia',
  'Baringo',
  'Turkana',
  'Narok',
  'Wajir',
  'Mandera',
  'Garissa',
  'Migori',
  'Homa Bay'
];

export const KENYAN_CROPS = [
  'Maize',
  'Wheat',
  'Rice',
  'Sorghum',
  'Millet',
  'Beans',
  'Peas',
  'Groundnuts',
  'Sunflower',
  'Soybean',
  'Coconut',
  'Tea',
  'Coffee',
  'Sugarcane',
  'Tomatoes',
  'Potatoes',
  'Onions',
  'Carrots',
  'Cabbage',
  'Spinach',
  'Kale',
  'Bananas',
  'Avocados',
  'Mangoes',
  'Citrus',
  'Papaya',
  'Pineapple',
  'Watermelon',
  'Passion Fruit',
  'Macadamia',
  'Cotton',
  'Tobacco',
  'Pyrethrum',
  'Horticulture'
];

// ============================================================================
// LIVESTOCK TYPES (NEW)
// ============================================================================

export const LIVESTOCK_TYPES = [
  'Dairy Cattle',
  'Beef Cattle',
  'Sheep',
  'Goats',
  'Poultry',
  'Fisheries',
  'Beekeeping',
  'Pigs',
  'Rabbits',
  'Donkeys',
  'Camels'
];

// ============================================================================
// KENYA CITIES (MAJOR URBAN CENTERS)
// ============================================================================

export const KENYAN_CITIES = [
  'Nairobi',
  'Mombasa',
  'Kisumu',
  'Nakuru',
  'Eldoret',
  'Kericho',
  'Nyeri',
  'Kiambu',
  'Naivasha',
  'Malindi',
  'Lamu',
  'Moshi',
  'Thika',
  'Isiolo',
  'Kisi',
  'Nyamira',
  'Bungoma',
  'Busia',
  'Kitale',
  'Garissa',
  'Wajir',
  'Mandera',
  'Embu',
  'Machakos',
  'Makueni',
  'Narok',
  'Kajiado',
  'Voi'
];

export const COOPERATIVE_TYPES = [
  'Marketing Cooperative',
  'Agricultural Cooperative',
  'Transport Cooperative',
  'Savings & Credit Cooperative',
  'Production Cooperative',
  'Service Cooperative',
  'Multi-Purpose Cooperative'
];

export const FARMING_METHODS = [
  'Organic',
  'Conventional',
  'Mixed',
  'Conservation Agriculture',
  'Agroforestry',
  'Precision Agriculture',
  'Hydroponics',
  'Greenhouse'
];

export const LENDER_TYPES = [
  'Commercial Bank',
  'Microfinance Institution',
  'Savings & Credit Cooperative',
  'Government',
  'NGO',
  'Private Lender',
  'Agricultural Development Bank'
];

// ============================================================================
// AUTH ENUMS
// ============================================================================

export enum AuthErrorCode {
  INVALID_CREDENTIALS = 'INVALID_CREDENTIALS',
  EMAIL_NOT_VERIFIED = 'EMAIL_NOT_VERIFIED',
  ACCOUNT_DISABLED = 'ACCOUNT_DISABLED',
  TOO_MANY_ATTEMPTS = 'TOO_MANY_ATTEMPTS',
  NETWORK_ERROR = 'NETWORK_ERROR',
  SESSION_EXPIRED = 'SESSION_EXPIRED',
  OAUTH_ERROR = 'OAUTH_ERROR',
  UNKNOWN_ERROR = 'UNKNOWN_ERROR'
}

export enum LoginMethod {
  EMAIL_PASSWORD = 'email_password',
  GOOGLE = 'google',
  GITHUB = 'github',
  MAGIC_LINK = 'magic_link',
  WEB3 = 'web3'
}

