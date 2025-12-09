-- =============================================================
-- MIGRATION SCRIPT: OLD DDL -> NEW DDL
-- DATABASE: PostgreSQL
-- =============================================================

BEGIN;

-- -------------------------------------------------------------
-- 1. PRE-CLEANING: Deduplication
-- -------------------------------------------------------------
-- We must remove duplicates before applying new UNIQUE constraints.

-- Clean `search_preference_interest`
DELETE FROM search_preference_interest a
USING search_preference_interest b
WHERE a.id > b.id
  AND a.fk_search_preference_id = b.fk_search_preference_id
  AND a.fk_interest_id = b.fk_interest_id;

-- Clean `user_interest`
DELETE FROM user_interest a
USING user_interest b
WHERE a.id > b.id
  AND a.fk_user_details_id = b.fk_user_details_id
  AND a.fk_interest_id = b.fk_interest_id;


-- -------------------------------------------------------------
-- 2. SUBSCRIPTION OWNERSHIP INVERSION (Complex)
-- -------------------------------------------------------------
-- Goal: Move relationship from Child (user_details) to Parent (subscription)

-- A. Add the column as nullable first
ALTER TABLE subscription ADD COLUMN fk_owner_id INTEGER;

-- B. Migrate Data
-- We arbitrarily pick ONE user (LIMIT 1) if multiple users shared a subscription.
UPDATE subscription s
SET fk_owner_id = (
    SELECT ud.id
    FROM user_details ud
    WHERE ud.fk_subscription_id = s.id
    LIMIT 1
);

-- C. Delete Orphans
-- Confirmed: Delete subscriptions that have no linked user.
DELETE FROM subscription WHERE fk_owner_id IS NULL;

-- D. Apply Constraints
ALTER TABLE subscription
    ALTER COLUMN fk_owner_id SET NOT NULL,
    ADD CONSTRAINT fk_subscription_owner
        FOREIGN KEY (fk_owner_id) REFERENCES user_details (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE;

-- E. Remove old relationship from user_details
ALTER TABLE user_details DROP COLUMN fk_subscription_id;


-- -------------------------------------------------------------
-- 3. REPORT -> ADMIN REFERENCE FIX
-- -------------------------------------------------------------
-- Goal: Remap fk_administrator_id from UserID to AdminID

-- A. Drop old constraint
ALTER TABLE "report" DROP CONSTRAINT report_fk_administrator_id_fkey;

-- B. Update Data
-- Map the stored UserID to the actual Administrator ID
UPDATE "report" r
SET fk_administrator_id = a.id
FROM administrator a
WHERE r.fk_administrator_id = a.fk_user_id;

-- C. Add new constraint referencing administrator(id)
ALTER TABLE "report"
    ADD CONSTRAINT report_fk_administrator_id_fkey
    FOREIGN KEY (fk_administrator_id) REFERENCES administrator (id)
    ON DELETE SET NULL
    ON UPDATE CASCADE;


-- -------------------------------------------------------------
-- 4. BLOCK TABLE RESTRUCTURING
-- -------------------------------------------------------------
-- Goal: Change PK from composite to Surrogate (ID)

-- A. Drop old PK
ALTER TABLE block DROP CONSTRAINT block_pkey;

-- B. Add new Identity Column
ALTER TABLE block ADD COLUMN id INTEGER GENERATED ALWAYS AS IDENTITY;

-- C. Set new PK
ALTER TABLE block ADD PRIMARY KEY (id);

-- D. Re-add the uniqueness logic as a constraint
ALTER TABLE block
    ADD CONSTRAINT block_unique_pair
    UNIQUE (fk_blocking_user_details_id, fk_blocked_user_details_id);


-- -------------------------------------------------------------
-- 5. STRUCTURAL ALTERATIONS & CLEANUP
-- -------------------------------------------------------------

-- Subscription Plan
ALTER TABLE subscription_plan
    ADD COLUMN max_users INTEGER DEFAULT 1 CHECK (max_users > 0);

-- Subscription
ALTER TABLE subscription
    ADD COLUMN updated_at TIMESTAMP DEFAULT now(),
    DROP COLUMN last_renewal, -- Confirmed Data Loss
    DROP COLUMN uploaded_at;

-- Search Preference Sex
ALTER TABLE search_preference_sex
    RENAME COLUMN priorty TO priority;

-- User Details
ALTER TABLE user_details
    ADD CONSTRAINT user_details_fk_user_id_key UNIQUE (fk_user_id);

-- Apply Unique Constraints to cleaned tables
ALTER TABLE search_preference_interest
    ADD CONSTRAINT search_preference_interest_unique_key
    UNIQUE (fk_search_preference_id, fk_interest_id);

ALTER TABLE user_interest
    ADD CONSTRAINT user_interest_unique_key
    UNIQUE (fk_user_details_id, fk_interest_id);


-- -------------------------------------------------------------
-- 6. VERIFICATION (Optional - for logging)
-- -------------------------------------------------------------
DO $$
BEGIN
    RAISE NOTICE 'Migration completed successfully. Tables transformed.';
END $$;

COMMIT;
