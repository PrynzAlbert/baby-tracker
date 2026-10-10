-- =====================================================================
-- Smart Baby Tracker - Complete Database Schema (Clean Slate)
-- =====================================================================
-- Drop all existing tables and recreate from scratch
-- Safe for development environments

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS public.baby_logs CASCADE;
DROP TABLE IF EXISTS public.profiles CASCADE;

-- =====================================================================
-- Profiles Table
-- =====================================================================
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    caregiver_name TEXT NOT NULL,
    baby_name TEXT NOT NULL,
    baby_dob TEXT NOT NULL, -- ISO format: YYYY-MM-DD
    family_id TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- =====================================================================
-- Baby Logs Table (optimized for tracking)
-- =====================================================================
CREATE TABLE public.baby_logs (
    id BIGSERIAL PRIMARY KEY,
    family_id TEXT NOT NULL,
    type TEXT NOT NULL, -- 'Feed', 'Sleep', 'Diaper', 'Note', 'Temperature', 'Weight', etc.
    created_by_caregiver TEXT NOT NULL,
    note TEXT,
    start_date_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date_time TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    
    -- Expandable fields for different log types
    feed_type TEXT, -- 'Breast Milk', 'Formula', 'Solid'
    amount_ml NUMERIC(10, 2),
    diaper_status TEXT, -- 'Wet', 'Dirty', 'Both'
    temperature_celsius NUMERIC(5, 2),
    weight_kg NUMERIC(6, 2),
    
    -- Import/Export metadata
    source_app TEXT DEFAULT 'smart_baby', -- 'smart_baby', 'nara', 'imported_csv', etc.
    external_id TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- =====================================================================
-- Indexes for Performance
-- =====================================================================
CREATE INDEX idx_baby_logs_family_id ON public.baby_logs(family_id);
CREATE INDEX idx_baby_logs_start_date_time ON public.baby_logs(start_date_time DESC);
CREATE INDEX idx_baby_logs_type ON public.baby_logs(type);
CREATE INDEX idx_baby_logs_family_date ON public.baby_logs(family_id, start_date_time DESC);
CREATE INDEX idx_baby_logs_source_app ON public.baby_logs(source_app);

-- =====================================================================
-- Enable Row Level Security (RLS)
-- =====================================================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.baby_logs ENABLE ROW LEVEL SECURITY;

-- =====================================================================
-- RLS Policies for Profiles
-- =====================================================================
CREATE POLICY "Users can view their own profile"
    ON public.profiles
    FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile"
    ON public.profiles
    FOR INSERT
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
    ON public.profiles
    FOR UPDATE
    USING (auth.uid() = id);

-- =====================================================================
-- RLS Policies for Baby Logs (family-scoped access)
-- =====================================================================
CREATE POLICY "Users can view their family's logs"
    ON public.baby_logs
    FOR SELECT
    USING (
        family_id IN (
            SELECT family_id FROM public.profiles 
            WHERE id = auth.uid()
        )
    );

CREATE POLICY "Users can insert logs for their family"
    ON public.baby_logs
    FOR INSERT
    WITH CHECK (
        family_id IN (
            SELECT family_id FROM public.profiles 
            WHERE id = auth.uid()
        )
    );

CREATE POLICY "Users can update logs for their family"
    ON public.baby_logs
    FOR UPDATE
    USING (
        family_id IN (
            SELECT family_id FROM public.profiles 
            WHERE id = auth.uid()
        )
    );

CREATE POLICY "Users can delete logs for their family"
    ON public.baby_logs
    FOR DELETE
    USING (
        family_id IN (
            SELECT family_id FROM public.profiles 
            WHERE id = auth.uid()
        )
    );

-- =====================================================================
-- Audit Functions & Triggers
-- =====================================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_baby_logs_updated_at
    BEFORE UPDATE ON public.baby_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- =====================================================================
-- Verify tables created successfully
-- =====================================================================
SELECT 'Setup Complete!' as status;
