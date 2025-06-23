-- TrustBooks Backend Database Schema
-- Create tables for invoices and bank statements

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum for parsing status
CREATE TYPE parsing_status AS ENUM ('Parsed', 'Error', 'Processing');

-- Invoices table
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_path TEXT NOT NULL,
    invoice_number TEXT,
    invoice_date DATE,
    vendor_name TEXT,
    vendor_gstin TEXT,
    taxable_value DECIMAL(15,2),
    gst_amount DECIMAL(15,2),
    invoice_total DECIMAL(15,2),
    payment_terms TEXT,
    invoice_currency TEXT,
    items JSONB,
    status parsing_status DEFAULT 'Processing',
    raw_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Bank statements table
CREATE TABLE bank_statements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_path TEXT NOT NULL,
    txn_date DATE,
    description TEXT,
    debit DECIMAL(15,2),
    credit DECIMAL(15,2),
    balance DECIMAL(15,2),
    account_number TEXT,
    mode TEXT,
    category TEXT,
    meta_data JSONB,
    status parsing_status DEFAULT 'Processing',
    raw_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_vendor_name ON invoices(vendor_name);
CREATE INDEX idx_invoices_invoice_date ON invoices(invoice_date);
CREATE INDEX idx_invoices_file_path ON invoices(file_path);

CREATE INDEX idx_bank_statements_status ON bank_statements(status);
CREATE INDEX idx_bank_statements_txn_date ON bank_statements(txn_date);
CREATE INDEX idx_bank_statements_account_number ON bank_statements(account_number);
CREATE INDEX idx_bank_statements_file_path ON bank_statements(file_path);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_invoices_updated_at 
    BEFORE UPDATE ON invoices 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bank_statements_updated_at 
    BEFORE UPDATE ON bank_statements 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 