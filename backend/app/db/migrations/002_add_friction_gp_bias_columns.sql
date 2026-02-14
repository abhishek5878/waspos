-- Add Friction Report and GP Bias columns to investment_memos
ALTER TABLE investment_memos ADD COLUMN IF NOT EXISTS friction_report TEXT;
ALTER TABLE investment_memos ADD COLUMN IF NOT EXISTS gp_bias_ignore_reasoning TEXT;
