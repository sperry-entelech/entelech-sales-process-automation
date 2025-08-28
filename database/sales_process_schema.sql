-- Entelech Sales Process Automation Database Schema
-- Complete end-to-end sales workflow from discovery to project kickoff

CREATE DATABASE IF NOT EXISTS entelech_sales_automation;
USE entelech_sales_automation;

-- ================================
-- DISCOVERY & QUALIFICATION
-- ================================

-- Discovery Call Capture
CREATE TABLE discovery_calls (
    call_id INT PRIMARY KEY AUTO_INCREMENT,
    prospect_id INT NOT NULL,
    call_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sales_rep VARCHAR(100) NOT NULL,
    
    -- Company Information
    company_name VARCHAR(200) NOT NULL,
    company_size ENUM('1-10', '11-50', '51-200', '201-500', '501-1000', '1000+') NOT NULL,
    industry VARCHAR(100) NOT NULL,
    annual_revenue ENUM('under_1m', '1m_5m', '5m_25m', '25m_100m', '100m_plus', 'not_disclosed'),
    
    -- Contact Information
    primary_contact_name VARCHAR(150) NOT NULL,
    primary_contact_email VARCHAR(255) NOT NULL,
    primary_contact_title VARCHAR(100) NOT NULL,
    decision_maker_name VARCHAR(150),
    decision_maker_title VARCHAR(100),
    technical_contact_name VARCHAR(150),
    technical_contact_email VARCHAR(255),
    
    -- Current State Analysis
    current_challenges TEXT NOT NULL,
    manual_processes TEXT NOT NULL,
    time_waste_hours_weekly INT DEFAULT 0,
    estimated_cost_inefficiency DECIMAL(10,2) DEFAULT 0.00,
    current_tools_systems TEXT,
    team_size_affected INT DEFAULT 0,
    
    -- Requirements & Goals
    primary_objectives TEXT NOT NULL,
    success_metrics TEXT NOT NULL,
    automation_priorities TEXT NOT NULL,
    integration_requirements TEXT,
    compliance_requirements TEXT,
    security_requirements TEXT,
    
    -- Business Case
    budget_range ENUM('under_25k', '25k_50k', '50k_100k', '100k_250k', '250k_plus', 'not_disclosed'),
    timeline_urgency ENUM('immediate', '1_month', '3_months', '6_months', '12_months'),
    decision_timeline ENUM('1_week', '2_weeks', '1_month', '3_months', '6_months'),
    roi_expectations TEXT,
    
    -- Qualification Scoring
    pain_level_score INT DEFAULT 0 CHECK (pain_level_score >= 0 AND pain_level_score <= 10),
    budget_authority_score INT DEFAULT 0 CHECK (budget_authority_score >= 0 AND budget_authority_score <= 10),
    timeline_urgency_score INT DEFAULT 0 CHECK (timeline_urgency_score >= 0 AND timeline_urgency_score <= 10),
    technical_fit_score INT DEFAULT 0 CHECK (technical_fit_score >= 0 AND technical_fit_score <= 10),
    overall_qualification_score INT DEFAULT 0 CHECK (overall_qualification_score >= 0 AND overall_qualification_score <= 100),
    
    -- Call Results
    call_duration_minutes INT DEFAULT 0,
    next_steps TEXT,
    follow_up_date TIMESTAMP NULL,
    call_recording_url VARCHAR(500),
    call_notes TEXT,
    
    -- Status
    call_status ENUM('scheduled', 'completed', 'no_show', 'rescheduled') DEFAULT 'completed',
    qualified_status ENUM('qualified', 'disqualified', 'nurture', 'pending_review') DEFAULT 'pending_review',
    disqualification_reason TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ================================
-- SOW & PRICING CONFIGURATION
-- ================================

-- Service Catalog
CREATE TABLE service_catalog (
    service_id INT PRIMARY KEY AUTO_INCREMENT,
    service_name VARCHAR(200) NOT NULL,
    service_category ENUM('automation_development', 'process_optimization', 'integration_setup', 'ongoing_management', 'consulting', 'training') NOT NULL,
    service_description TEXT NOT NULL,
    
    -- Pricing Structure
    base_price DECIMAL(10,2) NOT NULL,
    price_per_hour DECIMAL(8,2) DEFAULT 0.00,
    price_per_user DECIMAL(8,2) DEFAULT 0.00,
    price_per_integration DECIMAL(8,2) DEFAULT 0.00,
    
    -- Effort Estimation
    base_hours_required INT NOT NULL,
    complexity_multipliers JSON, -- Store complexity adjustment factors
    
    -- Deliverables
    standard_deliverables TEXT NOT NULL,
    optional_deliverables TEXT,
    
    -- Prerequisites
    prerequisites TEXT,
    dependencies TEXT,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Pricing Rules & Modifiers
CREATE TABLE pricing_rules (
    rule_id INT PRIMARY KEY AUTO_INCREMENT,
    rule_name VARCHAR(100) NOT NULL,
    rule_type ENUM('discount', 'premium', 'complexity_multiplier', 'volume_discount') NOT NULL,
    
    -- Conditions
    company_size_condition JSON,
    industry_condition JSON,
    budget_range_condition JSON,
    timeline_condition JSON,
    complexity_condition JSON,
    
    -- Adjustments
    percentage_adjustment DECIMAL(5,2) DEFAULT 0.00, -- e.g., -10.00 for 10% discount
    fixed_amount_adjustment DECIMAL(10,2) DEFAULT 0.00,
    
    -- Rules
    rule_description TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    priority_order INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Generated SOWs
CREATE TABLE generated_sows (
    sow_id INT PRIMARY KEY AUTO_INCREMENT,
    discovery_call_id INT NOT NULL,
    sow_version INT DEFAULT 1,
    
    -- Project Overview
    project_title VARCHAR(300) NOT NULL,
    project_description TEXT NOT NULL,
    business_objectives TEXT NOT NULL,
    success_criteria TEXT NOT NULL,
    
    -- Scope of Work
    included_services JSON NOT NULL, -- Array of service IDs and configurations
    deliverables TEXT NOT NULL,
    timeline_weeks INT NOT NULL,
    project_phases JSON, -- Phase breakdown with timelines
    
    -- Pricing Breakdown
    base_services_cost DECIMAL(12,2) NOT NULL,
    additional_services_cost DECIMAL(12,2) DEFAULT 0.00,
    complexity_adjustments DECIMAL(12,2) DEFAULT 0.00,
    discounts_applied DECIMAL(12,2) DEFAULT 0.00,
    total_project_cost DECIMAL(12,2) NOT NULL,
    
    -- Payment Structure
    payment_schedule JSON NOT NULL, -- Milestone-based payment schedule
    payment_terms VARCHAR(100) DEFAULT '30 days',
    
    -- Terms & Conditions
    exclusions TEXT,
    assumptions TEXT,
    change_request_process TEXT NOT NULL,
    acceptance_criteria TEXT NOT NULL,
    
    -- Status & Approval
    sow_status ENUM('draft', 'review', 'sent', 'approved', 'rejected', 'expired') DEFAULT 'draft',
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP NULL,
    approved_at TIMESTAMP NULL,
    expires_at TIMESTAMP NULL,
    
    -- File References
    sow_document_url VARCHAR(500),
    pricing_breakdown_url VARCHAR(500),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (discovery_call_id) REFERENCES discovery_calls(call_id)
);

-- ================================
-- CONTRACT MANAGEMENT
-- ================================

-- Contract Templates
CREATE TABLE contract_templates (
    template_id INT PRIMARY KEY AUTO_INCREMENT,
    template_name VARCHAR(200) NOT NULL,
    template_type ENUM('standard', 'enterprise', 'government', 'non_profit', 'international') NOT NULL,
    
    -- Template Content
    template_content LONGTEXT NOT NULL,
    variable_placeholders JSON, -- Define merge fields
    
    -- Legal Terms
    liability_cap_percentage DECIMAL(5,2) DEFAULT 100.00,
    warranty_period_months INT DEFAULT 12,
    termination_notice_days INT DEFAULT 30,
    governing_law VARCHAR(100) DEFAULT 'Delaware',
    dispute_resolution ENUM('arbitration', 'mediation', 'court') DEFAULT 'arbitration',
    
    -- Usage Rules
    min_contract_value DECIMAL(12,2) DEFAULT 0.00,
    max_contract_value DECIMAL(12,2) DEFAULT 999999999.99,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Generated Contracts
CREATE TABLE generated_contracts (
    contract_id INT PRIMARY KEY AUTO_INCREMENT,
    sow_id INT NOT NULL,
    template_id INT NOT NULL,
    contract_version INT DEFAULT 1,
    
    -- Contract Details
    contract_number VARCHAR(50) UNIQUE NOT NULL,
    contract_title VARCHAR(300) NOT NULL,
    
    -- Parties
    client_legal_name VARCHAR(300) NOT NULL,
    client_address TEXT NOT NULL,
    client_signatory_name VARCHAR(200) NOT NULL,
    client_signatory_title VARCHAR(100) NOT NULL,
    client_signatory_email VARCHAR(255) NOT NULL,
    
    provider_legal_name VARCHAR(300) NOT NULL DEFAULT 'Entelech LLC',
    provider_signatory_name VARCHAR(200) NOT NULL,
    provider_signatory_title VARCHAR(100) NOT NULL,
    
    -- Financial Terms
    total_contract_value DECIMAL(12,2) NOT NULL,
    payment_schedule JSON NOT NULL,
    late_payment_penalty_rate DECIMAL(5,2) DEFAULT 1.50,
    
    -- Project Terms
    project_start_date DATE NOT NULL,
    project_end_date DATE NOT NULL,
    contract_effective_date DATE NOT NULL,
    contract_expiration_date DATE NOT NULL,
    
    -- Generated Content
    contract_content LONGTEXT NOT NULL,
    contract_hash VARCHAR(256) NOT NULL, -- For integrity verification
    
    -- E-Signature Integration
    docusign_envelope_id VARCHAR(100),
    hellosign_signature_request_id VARCHAR(100),
    signature_provider ENUM('docusign', 'hellosign', 'adobe_sign', 'manual') DEFAULT 'docusign',
    
    -- Status Tracking
    contract_status ENUM('draft', 'review', 'sent_for_signature', 'partially_signed', 'fully_executed', 'expired', 'cancelled') DEFAULT 'draft',
    sent_for_signature_at TIMESTAMP NULL,
    client_signed_at TIMESTAMP NULL,
    provider_signed_at TIMESTAMP NULL,
    fully_executed_at TIMESTAMP NULL,
    
    -- Files
    signed_contract_url VARCHAR(500),
    original_contract_url VARCHAR(500),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (sow_id) REFERENCES generated_sows(sow_id),
    FOREIGN KEY (template_id) REFERENCES contract_templates(template_id)
);

-- ================================
-- PAYMENT PROCESSING
-- ================================

-- Payment Configurations
CREATE TABLE payment_configurations (
    config_id INT PRIMARY KEY AUTO_INCREMENT,
    contract_id INT NOT NULL,
    
    -- Payment Provider Setup
    payment_provider ENUM('stripe', 'square', 'paypal', 'bank_transfer', 'check') NOT NULL,
    provider_customer_id VARCHAR(200),
    provider_subscription_id VARCHAR(200),
    
    -- Payment Structure
    payment_type ENUM('one_time', 'milestone_based', 'subscription', 'hybrid') NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Milestone Payments
    payment_schedule JSON, -- Detailed payment schedule
    
    -- Subscription Details (if applicable)
    monthly_amount DECIMAL(10,2) DEFAULT 0.00,
    subscription_start_date DATE NULL,
    subscription_end_date DATE NULL,
    
    -- Automation Settings
    auto_invoice_enabled BOOLEAN DEFAULT TRUE,
    auto_payment_enabled BOOLEAN DEFAULT FALSE,
    late_fee_enabled BOOLEAN DEFAULT TRUE,
    reminder_days_before JSON DEFAULT '[7, 3, 1]',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (contract_id) REFERENCES generated_contracts(contract_id)
);

-- Payment Transactions
CREATE TABLE payment_transactions (
    transaction_id INT PRIMARY KEY AUTO_INCREMENT,
    config_id INT NOT NULL,
    
    -- Transaction Details
    transaction_type ENUM('invoice', 'payment', 'refund', 'late_fee', 'dispute') NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Payment Provider Details
    provider_transaction_id VARCHAR(200),
    provider_customer_id VARCHAR(200),
    payment_method ENUM('credit_card', 'bank_transfer', 'ach', 'wire', 'check', 'paypal') NOT NULL,
    
    -- Invoice Details (for invoices)
    invoice_number VARCHAR(100),
    invoice_due_date DATE NULL,
    milestone_description VARCHAR(500),
    
    -- Status Tracking
    transaction_status ENUM('pending', 'processing', 'completed', 'failed', 'cancelled', 'refunded', 'disputed') NOT NULL,
    failure_reason TEXT,
    
    -- Dates
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_date TIMESTAMP NULL,
    
    -- References
    related_transaction_id INT NULL, -- For refunds/disputes
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (config_id) REFERENCES payment_configurations(config_id),
    FOREIGN KEY (related_transaction_id) REFERENCES payment_transactions(transaction_id)
);

-- ================================
-- PROJECT KICKOFF AUTOMATION
-- ================================

-- Kickoff Templates
CREATE TABLE kickoff_templates (
    template_id INT PRIMARY KEY AUTO_INCREMENT,
    template_name VARCHAR(200) NOT NULL,
    service_category VARCHAR(100) NOT NULL,
    
    -- Kickoff Process
    kickoff_checklist JSON NOT NULL, -- Tasks and requirements
    required_client_information JSON NOT NULL, -- Info needed from client
    initial_deliverables JSON NOT NULL, -- What we deliver first
    
    -- Team Assignment Rules
    team_roles_required JSON NOT NULL, -- Roles needed for project
    estimated_team_size INT NOT NULL,
    project_manager_required BOOLEAN DEFAULT TRUE,
    technical_lead_required BOOLEAN DEFAULT TRUE,
    
    -- Communication Plan
    communication_schedule JSON, -- Meeting cadence and formats
    reporting_frequency ENUM('daily', 'weekly', 'bi_weekly', 'monthly') DEFAULT 'weekly',
    status_report_template TEXT,
    
    -- Tools & Access
    required_tools JSON, -- Tools needed for project
    client_access_requirements JSON, -- What access we need from client
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Project Kickoffs
CREATE TABLE project_kickoffs (
    kickoff_id INT PRIMARY KEY AUTO_INCREMENT,
    contract_id INT NOT NULL,
    template_id INT NOT NULL,
    
    -- Project Information
    project_code VARCHAR(50) UNIQUE NOT NULL,
    project_name VARCHAR(300) NOT NULL,
    project_manager VARCHAR(200) NOT NULL,
    technical_lead VARCHAR(200),
    
    -- Team Assignment
    assigned_team_members JSON, -- Team member assignments
    team_size INT DEFAULT 0,
    
    -- Kickoff Status
    kickoff_status ENUM('pending', 'in_progress', 'completed', 'on_hold') DEFAULT 'pending',
    kickoff_scheduled_date TIMESTAMP NULL,
    kickoff_completed_date TIMESTAMP NULL,
    
    -- Client Onboarding
    client_onboarding_completed BOOLEAN DEFAULT FALSE,
    client_access_granted BOOLEAN DEFAULT FALSE,
    tools_provisioned BOOLEAN DEFAULT FALSE,
    initial_discovery_completed BOOLEAN DEFAULT FALSE,
    
    -- Project Setup
    project_workspace_created BOOLEAN DEFAULT FALSE,
    communication_channels_setup BOOLEAN DEFAULT FALSE,
    documentation_initialized BOOLEAN DEFAULT FALSE,
    first_milestone_scheduled BOOLEAN DEFAULT FALSE,
    
    -- Deliverables Tracking
    kickoff_deliverables JSON, -- Initial deliverables status
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (contract_id) REFERENCES generated_contracts(contract_id),
    FOREIGN KEY (template_id) REFERENCES kickoff_templates(template_id)
);

-- ================================
-- PROCESS AUTOMATION LOGS
-- ================================

-- Workflow Automation Log
CREATE TABLE workflow_automation_log (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    
    -- Process Tracking
    process_type ENUM('discovery_to_sow', 'sow_to_contract', 'contract_to_payment', 'payment_to_kickoff') NOT NULL,
    source_record_id INT NOT NULL, -- ID of the triggering record
    target_record_id INT NULL, -- ID of the created record
    
    -- Automation Details
    automation_trigger VARCHAR(200) NOT NULL,
    automation_action VARCHAR(200) NOT NULL,
    automation_status ENUM('initiated', 'processing', 'completed', 'failed', 'manual_intervention_required') NOT NULL,
    
    -- Processing Info
    processing_start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_end_time TIMESTAMP NULL,
    processing_duration_seconds INT DEFAULT 0,
    
    -- Results
    automation_result JSON, -- Detailed results and data
    error_message TEXT NULL,
    manual_steps_required TEXT NULL,
    
    -- User Context
    triggered_by_user VARCHAR(200),
    approved_by_user VARCHAR(200),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================
-- CONFIGURATION & SETTINGS
-- ================================

-- System Configuration
CREATE TABLE system_configuration (
    config_key VARCHAR(100) PRIMARY KEY,
    config_value TEXT NOT NULL,
    config_description TEXT,
    config_type ENUM('string', 'number', 'boolean', 'json') DEFAULT 'string',
    is_editable BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert default configuration
INSERT INTO system_configuration (config_key, config_value, config_description, config_type) VALUES
('default_contract_template_id', '1', 'Default contract template to use', 'number'),
('auto_sow_generation_enabled', 'true', 'Enable automatic SOW generation after qualified discovery calls', 'boolean'),
('auto_contract_generation_enabled', 'true', 'Enable automatic contract generation after SOW approval', 'boolean'),
('auto_payment_setup_enabled', 'true', 'Enable automatic payment configuration after contract signing', 'boolean'),
('auto_kickoff_trigger_enabled', 'true', 'Enable automatic project kickoff after first payment', 'boolean'),
('default_payment_terms_days', '30', 'Default payment terms in days', 'number'),
('default_project_manager', 'Alex Thompson', 'Default project manager assignment', 'string'),
('contract_expiration_days', '30', 'Days until unsigned contracts expire', 'number'),
('late_payment_penalty_rate', '1.5', 'Monthly late payment penalty rate (%)', 'number'),
('auto_invoice_days_before_due', '7', 'Days before milestone to auto-generate invoice', 'number');

-- ================================
-- INDEXES FOR PERFORMANCE
-- ================================

CREATE INDEX idx_discovery_prospect ON discovery_calls(prospect_id);
CREATE INDEX idx_discovery_date ON discovery_calls(call_date);
CREATE INDEX idx_discovery_qualified ON discovery_calls(qualified_status);
CREATE INDEX idx_sow_discovery ON generated_sows(discovery_call_id);
CREATE INDEX idx_sow_status ON generated_sows(sow_status);
CREATE INDEX idx_contract_sow ON generated_contracts(sow_id);
CREATE INDEX idx_contract_status ON generated_contracts(contract_status);
CREATE INDEX idx_payment_config_contract ON payment_configurations(contract_id);
CREATE INDEX idx_payment_transaction_config ON payment_transactions(config_id);
CREATE INDEX idx_payment_status ON payment_transactions(transaction_status);
CREATE INDEX idx_kickoff_contract ON project_kickoffs(contract_id);
CREATE INDEX idx_kickoff_status ON project_kickoffs(kickoff_status);
CREATE INDEX idx_workflow_log_type ON workflow_automation_log(process_type);
CREATE INDEX idx_workflow_log_status ON workflow_automation_log(automation_status);