BEGIN;

-- FIX 1: Delete Orphan Subscriptions
-- Since no user claims these, they cannot be migrated to the new schema
-- where an owner is required.
DELETE FROM subscription
WHERE id IN (
    SELECT s.id
    FROM subscription s
    LEFT JOIN user_details ud ON s.id = ud.fk_subscription_id
    WHERE ud.id IS NULL
);

-- FIX 2: Handle Invalid Admin Reports (Set to NULL)
-- If a report references a user who is not an admin, we clear the field
-- rather than letting the migration fail or point to the wrong ID.
UPDATE "report" r
SET fk_administrator_id = NULL
WHERE fk_administrator_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM administrator a WHERE a.fk_user_id = r.fk_administrator_id
  );

-- FIX 3: (Optional) Handle Duplicate User Profiles
-- If Diagnostic 2 returned rows, you must delete duplicates manually.
-- This query keeps the most recently updated profile and deletes older ones.
-- UNCOMMENT TO RUN:
DELETE FROM user_details
WHERE id IN (
    SELECT id
    FROM (
        SELECT id,
               ROW_NUMBER() OVER (PARTITION BY fk_user_id ORDER BY updated_at DESC) as rn
        FROM user_details
        WHERE fk_user_id IS NOT NULL
    ) t
    WHERE t.rn > 1
);

COMMIT;
