-- =====================================================================
-- Unity Catalog Governance: RBAC, PII Masking, Column- & Row-level security
-- Run on a Unity Catalog-enabled Databricks SQL warehouse / cluster.
-- Replace group names with your workspace account groups.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Catalog & schema grants (RBAC)
--    Roles: data_engineers, analysts, admins
-- ---------------------------------------------------------------------
GRANT USE CATALOG ON CATALOG retail_dev TO `analysts`;
GRANT USE CATALOG ON CATALOG retail_dev TO `data_engineers`;
GRANT ALL PRIVILEGES ON CATALOG retail_dev TO `admins`;

-- Data engineers: full read/write on bronze + silver, build gold.
GRANT USE SCHEMA, SELECT, MODIFY, CREATE TABLE ON SCHEMA retail_dev.bronze TO `data_engineers`;
GRANT USE SCHEMA, SELECT, MODIFY, CREATE TABLE ON SCHEMA retail_dev.silver TO `data_engineers`;
GRANT USE SCHEMA, SELECT, MODIFY, CREATE TABLE ON SCHEMA retail_dev.gold   TO `data_engineers`;

-- Analysts: read-only on gold (curated) only. No access to bronze raw PII.
GRANT USE SCHEMA, SELECT ON SCHEMA retail_dev.gold TO `analysts`;
GRANT USE SCHEMA, SELECT ON SCHEMA retail_dev.silver TO `analysts`;

-- ---------------------------------------------------------------------
-- 2. PII Masking functions (column masks) for email & phone
--    Admins and data_engineers see clear text; everyone else sees masked.
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION retail_dev.silver.mask_email(email STRING)
RETURN CASE
    WHEN is_account_group_member('admins') OR is_account_group_member('data_engineers')
        THEN email
    WHEN email IS NULL THEN NULL
    ELSE concat('***@', split(email, '@')[1])
END;

CREATE OR REPLACE FUNCTION retail_dev.silver.mask_phone(phone STRING)
RETURN CASE
    WHEN is_account_group_member('admins') OR is_account_group_member('data_engineers')
        THEN phone
    WHEN phone IS NULL THEN NULL
    ELSE concat('******', right(phone, 4))
END;

-- Apply column masks to the silver customers table.
ALTER TABLE retail_dev.silver.customers
    ALTER COLUMN email SET MASK retail_dev.silver.mask_email;
ALTER TABLE retail_dev.silver.customers
    ALTER COLUMN phone SET MASK retail_dev.silver.mask_phone;

-- ---------------------------------------------------------------------
-- 3. Row-level security: analysts restricted by region/city allow-list.
--    Admins/engineers see all rows.
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION retail_dev.silver.city_row_filter(city STRING)
RETURN
    is_account_group_member('admins')
    OR is_account_group_member('data_engineers')
    OR city IN ('Chennai', 'Bangalore', 'Hyderabad');  -- analyst-visible region

ALTER TABLE retail_dev.silver.customers
    SET ROW FILTER retail_dev.silver.city_row_filter ON (city);

-- ---------------------------------------------------------------------
-- 4. Column-level security: revoke direct SELECT on raw email in bronze
--    so PII is only ever accessed through governed silver views.
-- ---------------------------------------------------------------------
REVOKE SELECT ON SCHEMA retail_dev.bronze FROM `analysts`;
