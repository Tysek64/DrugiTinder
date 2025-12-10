-- =========================================================
-- DIAGNOSTIC 1: Find Orphan Subscriptions (THE BLOCKER)
-- =========================================================
-- These are subscriptions that no user_details record points to.
-- These MUST be deleted or assigned to a dummy user before migration.
SELECT s.id AS subscription_id, s.expiration_date, s.is_active
FROM subscription s
LEFT JOIN user_details ud ON s.id = ud.fk_subscription_id
WHERE ud.id IS NULL;

-- =========================================================
-- DIAGNOSTIC 2: Find Duplicate User Links
-- =========================================================
-- The new schema requires user_details.fk_user_id to be UNIQUE.
-- If this returns rows, you have multiple profiles linked to one login.
SELECT fk_user_id, COUNT(*)
FROM user_details
WHERE fk_user_id IS NOT NULL
GROUP BY fk_user_id
HAVING COUNT(*) > 1;

-- =========================================================
-- DIAGNOSTIC 3: Find Invalid Admin Reports
-- =========================================================
-- The migration assumes report.fk_administrator_id points to a User ID
-- that exists in the administrator table. If this returns rows,
-- you have reports linked to users who are NOT admins.
SELECT r.id AS report_id, r.fk_administrator_id AS referenced_user_id
FROM report r
LEFT JOIN administrator a ON r.fk_administrator_id = a.fk_user_id
WHERE r.fk_administrator_id IS NOT NULL
  AND a.id IS NULL;
