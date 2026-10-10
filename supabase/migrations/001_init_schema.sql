-- =====================================================================
-- Smart Baby Tracker - Database Schema Migration
-- Add missing columns and set up proper constraints
-- =====================================================================

-- Drop the old baby_logs table if it exists (we'll recreate it properly)
DROP TABLE IF EXISTS public.baby_logs CASCADE;

-- Recreate baby_logs with the proper schema
CREATE TABLE public.baby_logs (
    id BIGSERIAL PRIMARY KEY,
    family_id TEXT NOT NULL,
    type TEXT NOT NULL, -- 'Feed', 'Sleep', 'Diaper', 'Note', 'Temperature', 'Weight', etc.
    created_by_caregiver TEXT NOT NULL,
    note TEXT,
    start_date_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date_time TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER, -- for Sleep, Activities
    
    -- Expandable fields for different log types
    feed_type TEXT, -- 'Breast Milk', 'Formula', 'Solid'
    amount_ml FLOAT, -- for Feed
    diaper_status TEXT, -- 'Wet', 'Dirty', 'Both'
    temperature_celsius FLOAT,
    weight_kg FLOAT,
    
    -- Import/Export metadata
    source_app TEXT DEFAULT 'smart_baby', -- 'smart_baby', 'nara', 'imported_csv', etc.
    external_id TEXT, -- ID from external app (for Nara compatibility)
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Indexes for performance
CREATE INDEX idx_baby_logs_family_id ON public.baby_logs(family_id);
CREATE INDEX idx_baby_logs_start_date_time ON public.baby_logs(start_date_time DESC);
CREATE INDEX idx_baby_logs_type ON public.baby_logs(type);
CREATE INDEX idx_baby_logs_family_date ON public.baby_logs(family_id, start_date_time DESC);
CREATE INDEX idx_baby_logs_source_app ON public.baby_logs(source_app);

-- Enable RLS
ALTER TABLE public.baby_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for baby_logs (view and edit logs for your family)
DROP POLICY IF EXISTS "Users can view their family's logs" ON public.baby_logs;
CREATE POLICY "Users can view their family's logs"
    ON public.baby_logs
    FOR SELECT
    USING (
        family_id IN (
            SELECT family_id FROM public.profiles 
            WHERE id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can insert logs for their family" ON public.baby_logs;
CREATE POLICY "Users can insert logs for their family"
    ON public.baby_logs
    FOR INSERT
    WITH CHECK (
        family_id IN (
            SELECT family_id FROM public.profiles 
            WHERE id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can update logs for their family" ON public.baby_logs;
CREATE POLICY "Users can update logs for their family"
    ON public.baby_logs
    FOR UPDATE
    USING (
        family_id IN (
            SELECT family_id FROM public.profiles 
            WHERE id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can delete logs for their family" ON public.baby_logs;
CREATE POLICY "Users can delete logs for their family"
    ON public.baby_logs
    FOR DELETE
    USING (
        family_id IN (
            SELECT family_id FROM public.profiles 
            WHERE id = auth.uid()
        )
    );

-- Audit trigger to update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_baby_logs_updated_at ON public.baby_logs;
CREATE TRIGGER update_baby_logs_updated_at
    BEFORE UPDATE ON public.baby_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
