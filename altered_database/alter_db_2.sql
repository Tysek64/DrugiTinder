BEGIN;

-- ======================================================================
-- PRECHECKS
-- ======================================================================

-- (Optional sanity checks you can uncomment)
-- SELECT current_database();

-- ======================================================================
-- STEP 1: subscription_plan.max_users
-- ======================================================================

ALTER TABLE IF EXISTS subscription_plan
  ADD COLUMN IF NOT EXISTS max_users INTEGER DEFAULT 1 CHECK (max_users > 0);

-- ======================================================================
-- STEP 2: subscription table migration
-- Add columns → backfill → validate → enforce NOT NULL → add constraints
-- ======================================================================

ALTER TABLE IF EXISTS subscription
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT now(),
  ADD COLUMN IF NOT EXISTS fk_owner_id INT,
  ADD COLUMN IF NOT EXISTS priority INT,
  ADD COLUMN IF NOT EXISTS id BIGINT;

-- Backfill fk_owner_id from commonly named columns
UPDATE subscription
SET fk_owner_id = COALESCE(
    (CASE WHEN EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = 'subscription'::regclass AND attname = 'owner_id') THEN owner_id END),
    (CASE WHEN EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = 'subscription'::regclass AND attname = 'user_id') THEN user_id END),
    (CASE WHEN EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = 'subscription'::regclass AND attname = 'fk_user_id') THEN fk_user_id END)
)
WHERE fk_owner_id IS NULL;

-- Validate fk_owner_id is fully populated
DO $$
DECLARE
  c INT;
BEGIN
  SELECT COUNT(*) INTO c FROM subscription WHERE fk_owner_id IS NULL;
  IF c > 0 THEN
    RAISE EXCEPTION 'fk_owner_id still contains % NULL rows — fix before migration.', c;
  END IF;
END$$;

-- Create sequence for id if missing
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_class WHERE relname = 'subscription_id_seq'
  ) THEN
    CREATE SEQUENCE subscription_id_seq OWNED BY subscription.id;
  END IF;
END$$;

UPDATE subscription
SET id = nextval('subscription_id_seq')
WHERE id IS NULL;

ALTER TABLE subscription ALTER COLUMN id SET DEFAULT nextval('subscription_id_seq');

-- Add PK if missing
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conrelid='subscription'::regclass AND contype='p'
  ) THEN
    ALTER TABLE subscription ADD CONSTRAINT subscription_pkey PRIMARY KEY (id);
  END IF;
END$$;

-- fk_owner_id → make NOT NULL
ALTER TABLE subscription ALTER COLUMN fk_owner_id SET NOT NULL;

-- Add FK to users or user_details
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_class WHERE relname='users') THEN
    ALTER TABLE subscription
      ADD CONSTRAINT subscription_fk_owner_id_fkey
      FOREIGN KEY (fk_owner_id) REFERENCES users(id)
      ON DELETE RESTRICT ON UPDATE CASCADE;

  ELSIF EXISTS (SELECT 1 FROM pg_class WHERE relname='user_details') THEN
    ALTER TABLE subscription
      ADD CONSTRAINT subscription_fk_owner_id_fkey
      FOREIGN KEY (fk_owner_id) REFERENCES user_details(id)
      ON DELETE RESTRICT ON UPDATE CASCADE;

  ELSE
    RAISE EXCEPTION 'Could not find users or user_details table to reference.';
  END IF;
END$$;

-- ======================================================================
-- STEP 3: UNIQUE constraint: blocking_user_details
-- ======================================================================

DO $$
DECLARE duplicates INT;
BEGIN
  IF EXISTS (SELECT 1 FROM pg_class WHERE relname='blocking_user_details') THEN

    SELECT COUNT(*) INTO duplicates FROM (
      SELECT fk_blocking_user_details_id, fk_blocked_user_details_id, COUNT(*)
      FROM blocking_user_details
      GROUP BY fk_blocking_user_details_id, fk_blocked_user_details_id
      HAVING COUNT(*) > 1
    ) d;

    IF duplicates > 0 THEN
      RAISE EXCEPTION 'Duplicate FK pairs detected: % rows. Resolve before adding UNIQUE.', duplicates;
    END IF;

    ALTER TABLE blocking_user_details
      ADD CONSTRAINT blocking_user_details_unique_pair
      UNIQUE (fk_blocking_user_details_id, fk_blocked_user_details_id);

  END IF;
END$$;

-- ======================================================================
-- STEP 4: Migrate report.fk_administrator_id → administrator(id)
-- ======================================================================

ALTER TABLE IF EXISTS report
  ADD COLUMN IF NOT EXISTS fk_administrator_id_new INT;

UPDATE report r
SET fk_administrator_id_new = a.id
FROM administrator a
WHERE r.fk_administrator_id = a.fk_user_id
  AND r.fk_administrator_id_new IS NULL;

DO $$
DECLARE m INT;
BEGIN
  SELECT COUNT(*) INTO m
  FROM report
  WHERE fk_administrator_id_new IS NULL AND fk_administrator_id IS NOT NULL;

  IF m > 0 THEN
    RAISE EXCEPTION '% report rows could not be mapped to administrator.id', m;
  END IF;
END$$;

ALTER TABLE report DROP CONSTRAINT IF EXISTS report_fk_administrator_id_fkey;
ALTER TABLE report DROP COLUMN IF EXISTS fk_administrator_id;
ALTER TABLE report RENAME COLUMN fk_administrator_id_new TO fk_administrator_id;

ALTER TABLE report
  ADD CONSTRAINT report_fk_administrator_id_fkey
  FOREIGN KEY (fk_administrator_id) REFERENCES administrator(id)
  ON DELETE SET NULL ON UPDATE CASCADE;

COMMIT;

