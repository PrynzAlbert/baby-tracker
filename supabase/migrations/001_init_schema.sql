-- =====================================================================
-- Smart Baby Tracker - Database Schema
-- =====================================================================

-- Profiles Table
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY,
    caregiver_name TEXT NOT NULL,
    baby_name TEXT NOT NULL,
    baby_dob TEXT NOT NULL, -- ISO format: YYYY-MM-DD
    family_id TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Baby Logs Table (optimized for tracking)
CREATE TABLE IF NOT EXISTS public.baby_logs (
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
    source_app TEXT, -- 'smart_baby', 'nara', 'imported_csv', etc.
    external_id TEXT, -- ID from external app (for Nara compatibility)
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    
    -- Constraints
    CONSTRAINT fk_family_id FOREIGN KEY (family_id) REFERENCES public.profiles(family_id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_baby_logs_family_id ON public.baby_logs(family_id);
CREATE INDEX IF NOT EXISTS idx_baby_logs_start_date_time ON public.baby_logs(start_date_time DESC);
CREATE INDEX IF NOT EXISTS idx_baby_logs_type ON public.baby_logs(type);
CREATE INDEX IF NOT EXISTS idx_baby_logs_family_date ON public.baby_logs(family_id, start_date_time DESC);

-- Enable RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.baby_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for profiles
CREATE POLICY "Users can view their own profile" 
    ON public.profiles 
    FOR SELECT 
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
    ON public.profiles
    FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile"
    ON public.profiles
    FOR INSERT
    WITH CHECK (auth.uid() = id);

-- RLS Policies for baby_logs (view and edit logs for your family)
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

-- Audit trigger to update updated_at
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
