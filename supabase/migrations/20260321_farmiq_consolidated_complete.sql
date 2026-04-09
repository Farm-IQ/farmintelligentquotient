-- ============================================================================
-- FARMIQ COMPLETE DATABASE SCHEMA - CONSOLIDATED
-- Single unified migration file with core tables and indexes only
-- 
-- Includes:
-- - Core authentication & user management
-- - Farm management & agricultural data
-- - Utility token system
-- - M-Pesa payment integration
-- - USSD/SMS integration
-- - AI usage tracking
-- - Credit scoring & loans
-- 
-- SCOPE: Basic tables and indexes only
-- NO RLS POLICIES, TRIGGERS, FUNCTIONS, OR PROCEDURES
-- 
-- Created: 2026-03-21
-- Version: 2.0 Consolidated Complete
-- ============================================================================

-- ============================================================================
-- SECTION 0: EXTENSIONS
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- ============================================================================
-- SECTION 1: REFERENCE/LOOKUP TABLES
-- ============================================================================

-- Locations hierarchy for geographic data
CREATE TABLE IF NOT EXISTS public.locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_code VARCHAR(50) UNIQUE NOT NULL,
    location_name VARCHAR(255) NOT NULL,
    location_type VARCHAR(50),  -- country, county, subcounty, ward, village
    parent_location_id UUID REFERENCES public.locations(id),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_locations_code ON public.locations(location_code);
CREATE INDEX idx_locations_type ON public.locations(location_type);
CREATE INDEX idx_locations_parent ON public.locations(parent_location_id);
CREATE INDEX idx_locations_name ON public.locations(location_name);

-- Measurement units (kg, liters, acres, etc.)
CREATE TABLE IF NOT EXISTS public.measurement_units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unit_code VARCHAR(20) UNIQUE NOT NULL,
    unit_name VARCHAR(100) NOT NULL,
    unit_symbol VARCHAR(10),
    unit_category VARCHAR(50),
    conversion_to_base_unit DECIMAL(12, 4),
    base_unit_code VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_measurement_units_code ON public.measurement_units(unit_code);
CREATE INDEX idx_measurement_units_category ON public.measurement_units(unit_category);

-- Expense categories
CREATE TABLE IF NOT EXISTS public.expense_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_name VARCHAR(255) NOT NULL,
    category_code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    icon_emoji VARCHAR(10),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_expense_categories_code ON public.expense_categories(category_code);
CREATE INDEX idx_expense_categories_is_active ON public.expense_categories(is_active);

-- Revenue categories
CREATE TABLE IF NOT EXISTS public.revenue_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_name VARCHAR(255) NOT NULL,
    category_code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    icon_emoji VARCHAR(10),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_revenue_categories_code ON public.revenue_categories(category_code);
CREATE INDEX idx_revenue_categories_is_active ON public.revenue_categories(is_active);

-- Payment statuses
CREATE TABLE IF NOT EXISTS public.payment_statuses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status_name VARCHAR(100) NOT NULL,
    status_code VARCHAR(50) UNIQUE NOT NULL,
    is_final_status BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_payment_statuses_code ON public.payment_statuses(status_code);

-- Farm ownership statuses
CREATE TABLE IF NOT EXISTS public.farm_statuses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status_name VARCHAR(100) NOT NULL,
    status_code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_farm_statuses_code ON public.farm_statuses(status_code);

-- ============================================================================
-- SECTION 2: CORE USER MANAGEMENT
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.users (
    id TEXT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone_number VARCHAR(20),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    last_activity TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON public.users(email);
CREATE INDEX idx_users_phone ON public.users(phone_number);
CREATE INDEX idx_users_role ON public.users(role);
CREATE INDEX idx_users_is_active ON public.users(is_active);

-- User profiles with detailed information
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT REFERENCES public.users(id) ON DELETE CASCADE,
    farmiq_id VARCHAR(50) UNIQUE,
    phone_number VARCHAR(20),
    national_id VARCHAR(50),
    date_of_birth DATE,
    gender VARCHAR(20),
    county VARCHAR(100),
    subcounty VARCHAR(100),
    ward VARCHAR(100),
    village VARCHAR(100),
    role VARCHAR(50),
    profile_image_url TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_user_profiles_farmiq_id ON public.user_profiles(farmiq_id);
CREATE INDEX idx_user_profiles_user_id ON public.user_profiles(user_id);
CREATE INDEX idx_user_profiles_phone ON public.user_profiles(phone_number);
CREATE INDEX idx_user_profiles_role ON public.user_profiles(role);

-- ============================================================================
-- SECTION 3: FARM MANAGEMENT
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.farms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT REFERENCES public.users(id) ON DELETE CASCADE,
    farm_code VARCHAR(50) UNIQUE NOT NULL,
    farm_name VARCHAR(255) NOT NULL,
    location_id UUID REFERENCES public.locations(id),
    farm_size_acres DECIMAL(10, 2),
    total_farm_size_acres DECIMAL(10, 2),
    ownership_status_id UUID REFERENCES public.farm_statuses(id),
    farm_description TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_farms_user_id ON public.farms(user_id);
CREATE INDEX idx_farms_farm_code ON public.farms(farm_code);
CREATE INDEX idx_farms_location_id ON public.farms(location_id);

-- ============================================================================
-- SECTION 4: TOKEN & PAYMENT SYSTEMS
-- ============================================================================

-- User token balances
CREATE TABLE IF NOT EXISTS public.user_token_balances (
    user_id TEXT PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
    total_fiq DECIMAL(15, 2) DEFAULT 0,
    available_fiq DECIMAL(15, 2) DEFAULT 0,
    reserved_fiq DECIMAL(15, 2) DEFAULT 0,
    daily_limit_fiq DECIMAL(15, 2) DEFAULT 100,
    monthly_limit_fiq DECIMAL(15, 2) DEFAULT 1000,
    daily_usage_fiq DECIMAL(15, 2) DEFAULT 0,
    monthly_usage_fiq DECIMAL(15, 2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_token_balances_user_id ON public.user_token_balances(user_id);

-- Token usage log (audit trail)
CREATE TABLE IF NOT EXISTS public.token_usage_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT REFERENCES public.users(id) ON DELETE CASCADE,
    operation_type VARCHAR(50),
    service_type VARCHAR(100),
    amount_fiq DECIMAL(15, 2),
    balance_before DECIMAL(15, 2),
    balance_after DECIMAL(15, 2),
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_token_usage_user_id ON public.token_usage_log(user_id);
CREATE INDEX idx_token_usage_operation ON public.token_usage_log(operation_type);
CREATE INDEX idx_token_usage_created_at ON public.token_usage_log(created_at DESC);
CREATE INDEX idx_token_usage_service ON public.token_usage_log(service_type);

-- ============================================================================
-- SECTION 5: M-PESA INTEGRATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.mpesa_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT REFERENCES public.users(id) ON DELETE SET NULL,
    request_id VARCHAR(255) UNIQUE,
    checkout_request_id VARCHAR(255),
    phone_number VARCHAR(20),
    transaction_type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'pending',
    amount_kes DECIMAL(12, 2),
    amount_fiq DECIMAL(15, 2),
    fiq_amount_minted DECIMAL(15, 2),
    mpesa_receipt_number VARCHAR(100),
    requested_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    response_code VARCHAR(50),
    response_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_mpesa_transactions_request_id ON public.mpesa_transactions(request_id);
CREATE INDEX idx_mpesa_transactions_phone_number ON public.mpesa_transactions(phone_number);
CREATE INDEX idx_mpesa_transactions_status ON public.mpesa_transactions(status);
CREATE INDEX idx_mpesa_transactions_user_id ON public.mpesa_transactions(user_id);
CREATE INDEX idx_mpesa_transactions_checkout_request_id ON public.mpesa_transactions(checkout_request_id);
CREATE INDEX idx_mpesa_transactions_mpesa_receipt ON public.mpesa_transactions(mpesa_receipt_number);
CREATE INDEX idx_mpesa_transactions_requested_at ON public.mpesa_transactions(requested_at DESC);

-- M-Pesa reversal requests
CREATE TABLE IF NOT EXISTS public.mpesa_reversal_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT REFERENCES public.users(id) ON DELETE SET NULL,
    request_id VARCHAR(255) UNIQUE,
    original_transaction_id UUID REFERENCES public.mpesa_transactions(id),
    phone_number VARCHAR(20),
    amount_kes DECIMAL(12, 2),
    reason VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    response_code VARCHAR(50),
    response_message TEXT,
    requested_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_mpesa_reversal_request_id ON public.mpesa_reversal_requests(request_id);
CREATE INDEX idx_mpesa_reversal_original_transaction_id ON public.mpesa_reversal_requests(original_transaction_id);
CREATE INDEX idx_mpesa_reversal_status ON public.mpesa_reversal_requests(status);
CREATE INDEX idx_mpesa_reversal_user_id ON public.mpesa_reversal_requests(user_id);

-- M-Pesa tax remittance
CREATE TABLE IF NOT EXISTS public.mpesa_tax_remittances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id VARCHAR(255) UNIQUE,
    account_number VARCHAR(100),
    account_type VARCHAR(50),
    amount_to_remit DECIMAL(12, 2),
    tax_period VARCHAR(20),
    prn VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    response_code VARCHAR(50),
    response_message TEXT,
    compliance_verified BOOLEAN DEFAULT FALSE,
    requested_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_mpesa_tax_request_id ON public.mpesa_tax_remittances(request_id);
CREATE INDEX idx_mpesa_tax_prn ON public.mpesa_tax_remittances(prn);
CREATE INDEX idx_mpesa_tax_status ON public.mpesa_tax_remittances(status);
CREATE INDEX idx_mpesa_tax_period ON public.mpesa_tax_remittances(tax_period);
CREATE INDEX idx_mpesa_tax_compliance_verified ON public.mpesa_tax_remittances(compliance_verified);

-- M-Pesa callback audit trail
CREATE TABLE IF NOT EXISTS public.mpesa_callbacks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    callback_type VARCHAR(100),
    request_id VARCHAR(255),
    conversation_id VARCHAR(255),
    raw_payload JSONB,
    processed BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_mpesa_callbacks_callback_type ON public.mpesa_callbacks(callback_type);
CREATE INDEX idx_mpesa_callbacks_request_id ON public.mpesa_callbacks(request_id);
CREATE INDEX idx_mpesa_callbacks_conversation_id ON public.mpesa_callbacks(conversation_id);
CREATE INDEX idx_mpesa_callbacks_received_at ON public.mpesa_callbacks(received_at DESC);
CREATE INDEX idx_mpesa_callbacks_processed ON public.mpesa_callbacks(processed);

-- M-Pesa balance history
CREATE TABLE IF NOT EXISTS public.mpesa_balance_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shortcode VARCHAR(10),
    account_number VARCHAR(100),
    account_type VARCHAR(50),
    working_account_balance DECIMAL(15, 2),
    utility_account_balance DECIMAL(15, 2),
    queried_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_mpesa_balance_shortcode ON public.mpesa_balance_history(shortcode);
CREATE INDEX idx_mpesa_balance_account_type ON public.mpesa_balance_history(account_type);
CREATE INDEX idx_mpesa_balance_queried_at ON public.mpesa_balance_history(queried_at DESC);

-- M-Pesa error log
CREATE TABLE IF NOT EXISTS public.mpesa_error_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_endpoint VARCHAR(255),
    request_payload JSONB,
    error_code VARCHAR(50),
    error_message TEXT,
    error_details JSONB,
    error_time TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_mpesa_error_log_api_endpoint ON public.mpesa_error_log(api_endpoint);
CREATE INDEX idx_mpesa_error_log_error_code ON public.mpesa_error_log(error_code);
CREATE INDEX idx_mpesa_error_log_error_time ON public.mpesa_error_log(error_time DESC);

-- ============================================================================
-- SECTION 6: USSD/SMS INTEGRATION
-- ============================================================================

-- USSD sessions
CREATE TABLE IF NOT EXISTS public.ussd_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    user_id TEXT REFERENCES public.users(id) ON DELETE SET NULL,
    service_code VARCHAR(50),
    network_code VARCHAR(50),
    current_menu VARCHAR(100) DEFAULT 'welcome',
    input_history TEXT[] DEFAULT '{}',
    session_data JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_interaction_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_ussd_sessions_session_id ON public.ussd_sessions(session_id);
CREATE INDEX idx_ussd_sessions_phone_number ON public.ussd_sessions(phone_number);
CREATE INDEX idx_ussd_sessions_status ON public.ussd_sessions(status);
CREATE INDEX idx_ussd_sessions_expires_at ON public.ussd_sessions(expires_at);

-- SMS delivery tracking
CREATE TABLE IF NOT EXISTS public.sms_delivery_track (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id VARCHAR(255) UNIQUE,
    phone_number VARCHAR(20) NOT NULL,
    user_id TEXT REFERENCES public.users(id) ON DELETE SET NULL,
    message_content TEXT,
    message_type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'pending',
    provider VARCHAR(50) DEFAULT 'afrikatalk',
    failed_reason TEXT,
    network_code VARCHAR(50),
    recipient_count INT DEFAULT 1,
    sender_id VARCHAR(100),
    attempted_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sms_delivery_track_message_id ON public.sms_delivery_track(message_id);
CREATE INDEX idx_sms_delivery_track_phone_number ON public.sms_delivery_track(phone_number);
CREATE INDEX idx_sms_delivery_track_status ON public.sms_delivery_track(status);
CREATE INDEX idx_sms_delivery_track_created_at ON public.sms_delivery_track(created_at DESC);
CREATE INDEX idx_sms_delivery_track_user_id ON public.sms_delivery_track(user_id);

-- SMS delivery reports
CREATE TABLE IF NOT EXISTS public.sms_delivery_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id VARCHAR(255) UNIQUE NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    status VARCHAR(50),
    failure_reason VARCHAR(255),
    retry_count INT DEFAULT 0,
    network_code VARCHAR(50),
    report_received_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sms_delivery_reports_message_id ON public.sms_delivery_reports(message_id);
CREATE INDEX idx_sms_delivery_reports_status ON public.sms_delivery_reports(status);

-- SMS opt-outs
CREATE TABLE IF NOT EXISTS public.sms_optouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) NOT NULL,
    sender_id VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    opted_out_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(phone_number, sender_id)
);

CREATE INDEX idx_sms_optouts_phone_number ON public.sms_optouts(phone_number);
CREATE INDEX idx_sms_optouts_sender_id ON public.sms_optouts(sender_id);
CREATE INDEX idx_sms_optouts_is_active ON public.sms_optouts(is_active);

-- USSD navigation audit
CREATE TABLE IF NOT EXISTS public.ussd_navigation_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255),
    phone_number VARCHAR(20),
    current_menu VARCHAR(100),
    user_input VARCHAR(500),
    action_type VARCHAR(100),
    response_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ussd_nav_audit_session_id ON public.ussd_navigation_audit(session_id);
CREATE INDEX idx_ussd_nav_audit_phone_number ON public.ussd_navigation_audit(phone_number);
CREATE INDEX idx_ussd_nav_audit_created_at ON public.ussd_navigation_audit(created_at DESC);
CREATE INDEX idx_ussd_nav_audit_action_type ON public.ussd_navigation_audit(action_type);

-- ============================================================================
-- SECTION 7: AI & USAGE TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.ai_usage_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT REFERENCES public.users(id) ON DELETE CASCADE,
    service_type VARCHAR(100),
    model_name VARCHAR(255),
    input_tokens INT,
    output_tokens INT,
    total_tokens INT,
    cost_fiq DECIMAL(15, 2),
    cost_kes DECIMAL(12, 2),
    response_time_ms INT,
    status VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ai_usage_user_id ON public.ai_usage_log(user_id);
CREATE INDEX idx_ai_usage_service ON public.ai_usage_log(service_type);
CREATE INDEX idx_ai_usage_model ON public.ai_usage_log(model_name);
CREATE INDEX idx_ai_usage_created_at ON public.ai_usage_log(created_at DESC);

-- ============================================================================
-- SECTION 8: CREDIT SCORING & LOANS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.fiq_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT REFERENCES public.users(id) ON DELETE CASCADE,
    farm_id UUID REFERENCES public.farms(id) ON DELETE SET NULL,
    fiq_score DECIMAL(5, 2),
    calculated_at TIMESTAMP WITH TIME ZONE,
    valid_until TIMESTAMP WITH TIME ZONE,
    risk_level VARCHAR(50),
    loan_eligible BOOLEAN,
    max_loan_amount_kes DECIMAL(15, 2),
    interest_rate_percent DECIMAL(5, 2),
    calculation_factors JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_fiq_scores_user_id ON public.fiq_scores(user_id);
CREATE INDEX idx_fiq_scores_farm_id ON public.fiq_scores(farm_id);
CREATE INDEX idx_fiq_scores_calculated_at ON public.fiq_scores(calculated_at DESC);
CREATE INDEX idx_fiq_scores_risk_level ON public.fiq_scores(risk_level);

-- ============================================================================
-- SECTION 9: CROP & PRODUCTION DATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.crops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID REFERENCES public.farms(id) ON DELETE CASCADE,
    crop_name VARCHAR(255) NOT NULL,
    crop_variety VARCHAR(255),
    planting_date DATE,
    expected_harvest_date DATE,
    actual_harvest_date DATE,
    area_planted_acres DECIMAL(10, 2),
    planting_unit_id UUID REFERENCES public.measurement_units(id),
    expected_yield DECIMAL(15, 2),
    actual_yield DECIMAL(15, 2),
    yield_unit_id UUID REFERENCES public.measurement_units(id),
    status VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_crops_farm_id ON public.crops(farm_id);
CREATE INDEX idx_crops_status ON public.crops(status);
CREATE INDEX idx_crops_planting_date ON public.crops(planting_date);

-- ============================================================================
-- SECTION 10: EXPENSES & REVENUES
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.farm_expenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID REFERENCES public.farms(id) ON DELETE CASCADE,
    crop_id UUID REFERENCES public.crops(id) ON DELETE SET NULL,
    category_id UUID REFERENCES public.expense_categories(id),
    expense_amount DECIMAL(15, 2),
    currency VARCHAR(10),
    expense_date DATE,
    description TEXT,
    vendor_name VARCHAR(255),
    payment_method VARCHAR(50),
    receipt_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_farm_expenses_farm_id ON public.farm_expenses(farm_id);
CREATE INDEX idx_farm_expenses_crop_id ON public.farm_expenses(crop_id);
CREATE INDEX idx_farm_expenses_category_id ON public.farm_expenses(category_id);
CREATE INDEX idx_farm_expenses_expense_date ON public.farm_expenses(expense_date DESC);

CREATE TABLE IF NOT EXISTS public.farm_revenues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID REFERENCES public.farms(id) ON DELETE CASCADE,
    crop_id UUID REFERENCES public.crops(id) ON DELETE SET NULL,
    category_id UUID REFERENCES public.revenue_categories(id),
    revenue_amount DECIMAL(15, 2),
    currency VARCHAR(10),
    revenue_date DATE,
    quantity_sold DECIMAL(15, 2),
    unit_price DECIMAL(15, 2),
    buyer_name VARCHAR(255),
    description TEXT,
    receipt_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_farm_revenues_farm_id ON public.farm_revenues(farm_id);
CREATE INDEX idx_farm_revenues_crop_id ON public.farm_revenues(crop_id);
CREATE INDEX idx_farm_revenues_category_id ON public.farm_revenues(category_id);
CREATE INDEX idx_farm_revenues_revenue_date ON public.farm_revenues(revenue_date DESC);

-- ============================================================================
-- SECTION 11: REFERENCE DATA POPULATION
-- ============================================================================

INSERT INTO public.measurement_units (unit_code, unit_name, unit_symbol, unit_category, conversion_to_base_unit, base_unit_code)
VALUES
    ('kg', 'Kilogram', 'kg', 'weight', 1.0, 'kg'),
    ('bag', '50kg Bag', 'bag', 'weight', 50.0, 'kg'),
    ('ton', 'Metric Ton', 'MT', 'weight', 1000.0, 'kg'),
    ('liters', 'Liters', 'L', 'volume', 1.0, 'liters'),
    ('acres', 'Acres', 'ac', 'area', 1.0, 'acres'),
    ('hectares', 'Hectares', 'ha', 'area', 2.47105, 'acres'),
    ('KES', 'Kenyan Shilling', 'KES', 'currency', 1.0, 'KES'),
    ('USD', 'US Dollar', 'USD', 'currency', 150.0, 'KES')
ON CONFLICT (unit_code) DO NOTHING;

INSERT INTO public.expense_categories (category_name, category_code, description, icon_emoji)
VALUES
    ('Seeds & Seedlings', 'SEEDS', 'Purchase of seeds and seedlings', '🌱'),
    ('Fertilizers', 'FERTILIZERS', 'Chemical and organic fertilizers', '🧪'),
    ('Pesticides', 'PESTICIDES', 'Pest control and fungicides', '🐛'),
    ('Labor', 'LABOR', 'Farm labor costs', '👨‍🌾'),
    ('Equipment', 'EQUIPMENT', 'Farm tools and machinery', '🔧'),
    ('Water', 'WATER', 'Irrigation and water costs', '💧'),
    ('Transport', 'TRANSPORT', 'Transport and logistics', '🚛'),
    ('Miscellaneous', 'MISC', 'Other expenses', '📋')
ON CONFLICT (category_code) DO NOTHING;

INSERT INTO public.revenue_categories (category_name, category_code, description, icon_emoji)
VALUES
    ('Crop Sales', 'CROP_SALES', 'Revenue from crop production', '🌾'),
    ('Livestock Sales', 'LIVESTOCK', 'Revenue from livestock', '🐄'),
    ('Contract Farming', 'CONTRACT', 'Contract farming income', '📝'),
    ('Agri Services', 'SERVICES', 'Agricultural services revenue', '🛠️'),
    ('Other Income', 'OTHER_INCOME', 'Miscellaneous income', '💰')
ON CONFLICT (category_code) DO NOTHING;

INSERT INTO public.payment_statuses (status_name, status_code, is_final_status)
VALUES
    ('Pending', 'PENDING', FALSE),
    ('Processing', 'PROCESSING', FALSE),
    ('Completed', 'COMPLETED', TRUE),
    ('Failed', 'FAILED', TRUE),
    ('Cancelled', 'CANCELLED', TRUE),
    ('Refunded', 'REFUNDED', TRUE)
ON CONFLICT (status_code) DO NOTHING;

INSERT INTO public.farm_statuses (status_name, status_code, description)
VALUES
    ('Owned', 'OWNED', 'Farm owned by the farmer'),
    ('Leased', 'LEASED', 'Farm leased by the farmer'),
    ('Communal', 'COMMUNAL', 'Communal farm'),
    ('Group', 'GROUP', 'Group farm'),
    ('Other', 'OTHER', 'Other ownership arrangement')
ON CONFLICT (status_code) DO NOTHING;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
