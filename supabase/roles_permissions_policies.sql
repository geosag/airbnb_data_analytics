------------------------------------------------------------------------------------
-- ROLE CREATION
------------------------------------------------------------------------------------

-- Created roles writer and reader to be used from the Python script and Power BI respectively

------------------------------------------------------------------------------------
-- PERMISSIONS
------------------------------------------------------------------------------------

-- Grant usage permission on public schema to writer role
GRANT USAGE ON SCHEMA public TO writer;

-- Grant usage permission on public schema to reader role
GRANT USAGE ON SCHEMA public TO reader;

-- Permissions to grant to writer role 
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO writer;

-- Permissions to grant to writer role 
GRANT SELECT ON ALL TABLES IN SCHEMA public TO reader;

------------------------------------------------------------------------------------
-- RLS --> ON: POLICIES FOR THE DIFFERENT ROLES IN EACH OF THE TABLES
------------------------------------------------------------------------------------

-- Allow writer to do everything on listings
CREATE POLICY "writer_all" ON listings
FOR ALL
TO writer
USING (true)
WITH CHECK (true);
  
-- Allow writer to do everything on reviews
CREATE POLICY "writer_all" ON reviews
FOR ALL
TO writer
USING (true)
WITH CHECK (true);

-- Allow writer to do everything on airbnb_data_latest_info
CREATE POLICY "writer_all" ON airbnb_data_latest_info
FOR ALL
TO writer
USING (true)
WITH CHECK (true);

-- Allow reader to only read on listings
CREATE POLICY "reader_select" ON listings
FOR SELECT
TO reader
USING (true);
  
-- Allow reader to only read on reviews
CREATE POLICY "reader_select" ON reviews
FOR SELECT
TO reader
USING (true);

-- Allow reader to only read on airbnb_data_latest_info
CREATE POLICY "reader_select" ON airbnb_data_latest_info
FOR SELECT
TO reader
USING (true);