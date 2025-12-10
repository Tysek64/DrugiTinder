BEGIN;

-- 1. MISC
-- 1.1 add: subscription_plan.max_users
ALTER TABLE subscription_plan
ADD COLUMN IF NOT EXISTS max_users INTEGER DEFAULT 1 CHECK (max_users > 0);

-- 1.2 fix: typo in search_preference_sex
DO $$
BEGIN
  IF EXISTS(SELECT 1
    FROM information_schema.columns
    WHERE table_name='search_preference_sex' 
      AND column_name='priorty')
  THEN
    ALTER TABLE "public"."search_preference_sex" 
      RENAME COLUMN "priorty" TO "priority";
  END IF;
END $$;

-- 1.3 add: UNIQUE constraint to the user_details.fk_user_id
-- also purge user_details if more than 1 are pointing to one user
WITH chosen AS (
    SELECT DISTINCT ON (fk_user_id)
        id, fk_user_id
    FROM user_details
    WHERE fk_subscription_id IS NOT NULL
    ORDER BY fk_user_id, id ASC
),
fallback AS (
    SELECT DISTINCT ON (fk_user_id)
        id, fk_user_id
    FROM user_details
    WHERE fk_user_id NOT IN (SELECT fk_user_id FROM chosen)
    ORDER BY fk_user_id, id ASC
),
final_keep AS (
    SELECT id FROM chosen
    UNION
    SELECT id FROM fallback
)
DELETE FROM user_details ud
WHERE ud.id NOT IN (SELECT id FROM final_keep);

ALTER TABLE user_details
ADD UNIQUE (fk_user_id);

-- 2. SUBSCRIPTION
-- 2.1. add: columns
ALTER TABLE subscription
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT now(),
ADD COLUMN IF NOT EXISTS fk_owner_id INTEGER;

-- 2.2 backfill: fk_owner_id
UPDATE subscription s
SET fk_owner_id = (
    SELECT ud.id
    FROM user_details ud
    WHERE ud.fk_subscription_id = s.id
    ORDER BY ud.id ASC
    LIMIT 1
)
WHERE fk_owner_id IS NULL
  AND EXISTS (
    SELECT 1
    FROM user_details ud
    WHERE ud.fk_subscription_id = s.id
  );
DELETE FROM subscription WHERE fk_owner_id IS NULL;

-- 2.3 add: constraints
ALTER TABLE subscription
ALTER COLUMN fk_owner_id SET NOT NULL;

ALTER TABLE subscription
ADD CONSTRAINT fk_subscription_owner
FOREIGN KEY (fk_owner_id) REFERENCES user_details (id)
ON DELETE CASCADE
ON UPDATE CASCADE;

-- 3. REPORT FK RE-MAPPING
-- 3.1 add: new admin id foreign key
ALTER TABLE report ADD COLUMN fk_administrator_id_new INT;

-- 3.2 drop: old FK contraint
ALTER TABLE report
DROP CONSTRAINT IF EXISTS report_fk_administrator_id_fkey;

-- 3.3 map old admin.fk_user_id ref to new admin.id ref 
UPDATE report r
SET fk_administrator_id_new = a.id
FROM administrator a
WHERE r.fk_administrator_id = a.fk_user_id;

DO $$
  DECLARE
    count_unmapped INT;
  BEGIN
    SELECT count(*)
    INTO count_unmapped
    FROM report
    WHERE fk_administrator_id IS NOT NULL
    AND fk_administrator_id_new IS NULL;

    IF count_unmapped > 0 THEN
      RAISE EXCEPTION
        'Migration aborted: % report rows cannot
        map old administrator (fk_user_id) to new administrator(id). 
        Fix data before proceeding.',
        count_unmapped;
    END IF;
END$$;

ALTER TABLE report
DROP COLUMN fk_administrator_id;

ALTER TABLE report
RENAME COLUMN fk_administrator_id_new TO fk_administrator_id;

-- 3.4: re-apply the FK to the fk_administrator_id, 
-- pointing to a new column
ALTER TABLE report
ADD CONSTRAINT report_fk_administrator_id_fkey
FOREIGN KEY (fk_administrator_id) REFERENCES administrator (id)
ON DELETE SET NULL
ON UPDATE CASCADE;

COMMIT;
