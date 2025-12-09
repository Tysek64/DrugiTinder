-- ==========================================================
-- 1. Raport: Lista wszystkich aktywnych użytkowników z ich imionami, nazwiskami, miastami i planami subskrypcji 
-- ==========================================================
SELECT 
    u.name, 
    u.surname, 
    c.name AS city_name,
    subscription_plan.name AS subscription_plan
FROM "user_details" u
LEFT JOIN city c ON u.fk_city_id = c.id
LEFT JOIN subscription ON u.fk_subscription_id = subscription.id
LEFT JOIN subscription_plan ON subscription.fk_subscription_plan_id = subscription_plan.id
ORDER BY u.surname, u.name;

-- ==========================================================
-- 2. Raport: Liczba użytkowników według płci w systemie
-- ==========================================================
SELECT s.name AS sex, COUNT(u.id) AS user_count
FROM "user_details" u
JOIN sex s ON u.fk_sex_id = s.id
GROUP BY s.name
ORDER BY user_count DESC;

-- ==========================================================
-- 3. Raport: Subskrypcje wygasające w ciągu najbliższych 30 dni
-- ==========================================================
SELECT u.name, u.surname, sp.name AS plan_name, s.expiration_date
FROM "user_details" u
JOIN subscription s ON u.fk_subscription_id = s.id
JOIN subscription_plan sp ON s.fk_subscription_plan_id = sp.id
WHERE s.expiration_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
ORDER BY s.expiration_date;

-- ==========================================================
-- 4. Raport: Liczba dopasowań każdego użytkownika – ranking popularności
-- ==========================================================
SELECT u.id, u.name, u.surname, COUNT(m_all.id) AS match_count
FROM "user_details" u
LEFT JOIN (
    SELECT fk_person1_id AS user_id, id FROM "match"
    UNION ALL
    SELECT fk_person2_id AS user_id, id FROM "match"
) m_all ON u.id = m_all.user_id
GROUP BY u.id, u.name, u.surname
ORDER BY match_count DESC;


-- ==========================================================
-- 5. Raport: Wszystkie wiadomości z ostatnich 7 dni
-- ==========================================================
SELECT 
    u.name,
    u.surname,
    m.id AS message_id, 
    m.contents, 
    m.send_time, 
    c.chat_theme
FROM message m
JOIN conversation c ON m.fk_conversation_id = c.id
JOIN user_details u ON m.fk_sender_id = u.id
WHERE m.send_time >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY m.send_time DESC;


-- ==========================================================
-- 6. Raport: Liczba wiadomości w każdej rozmowie – analiza aktywności
-- ==========================================================
SELECT c.id AS conversation_id, COUNT(m.id) AS message_count
FROM conversation c
LEFT JOIN message m ON c.id = m.fk_conversation_id
GROUP BY c.id
ORDER BY message_count DESC;

-- ==========================================================
-- 7. Raport: Użytkownicy z najdroższym planem subskrypcji
-- ==========================================================
SELECT 
    u.name,
    u.surname,
    sp.name AS plan_name,
    sp.price
FROM user_details u
JOIN subscription s ON u.fk_subscription_id = s.id
JOIN subscription_plan sp ON s.fk_subscription_plan_id = sp.id
WHERE sp.price = (SELECT MAX(price) FROM subscription_plan)
ORDER BY u.surname, u.name;



-- ==========================================================
-- 8. Raport: Liczba aktywnych blokad, które ma nałożone użytkownik 
-- ==========================================================

SELECT u.name, u.surname, COUNT(b.fk_blocked_user_details_id) AS active_blocks
FROM "user_details" u
LEFT JOIN block b ON u.id = b.fk_blocked_user_details_id AND b.is_active = TRUE
GROUP BY u.name, u.surname
ORDER BY active_blocks DESC;

-- ==========================================================
-- 9. Raport: Lista użytkowników, którzy zostali zbanowani, wraz z powodem i datą
-- ==========================================================
SELECT u.name, u.surname, r.reason, b.start_date, b.period_days
FROM ban b
JOIN "user_details" u ON b.fk_user_details_id = u.id
JOIN "report" r ON b.fk_report_id = r.id
ORDER BY b.start_date DESC;

-- ==========================================================
-- 10. Raport: Średni poziom zainteresowania użytkowników konkretnymi hobby
-- ==========================================================
SELECT i.name AS interest, ROUND(AVG(ui.level_of_interest), 2) AS avg_interest
FROM user_interest ui
JOIN interest i ON ui.fk_interest_id = i.id
GROUP BY i.name
ORDER BY avg_interest DESC;

-- ==========================================================
-- 11. Raport: Użytkownicy z automatycznym odnawianiem subskrypcji
-- ==========================================================
SELECT u.name, u.surname, sp.name AS plan_name
FROM "user_details" u
JOIN subscription s ON u.fk_subscription_id = s.id
JOIN subscription_plan sp ON s.fk_subscription_plan_id = sp.id
WHERE s.auto_renewal = TRUE;

-- ==========================================================
-- 12. Raport: Najbardziej aktywni użytkownicy w ostatnich 30 dniach
-- ==========================================================
SELECT 
    u.id,
    u.name,
    u.surname,
    COUNT(DISTINCT s.id) AS swipes_count,
    COUNT(DISTINCT m.id) AS messages_count,
    (COUNT(DISTINCT s.id) + COUNT(DISTINCT m.id)) AS total_activity
FROM user_details u
LEFT JOIN swipe s ON u.id = s.fk_swiping_user_details_id
                  AND s.swipe_time >= CURRENT_DATE - INTERVAL '30 days'
LEFT JOIN message m ON u.id = m.fk_sender_id
                   AND m.send_time >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY u.id, u.name, u.surname
ORDER BY total_activity DESC
LIMIT 20;


-- ==========================================================
-- 13. Raport: Ranking popularności zainteresowań – z iloma dopasowaniami wiążą się konkretne hobby
-- ==========================================================
WITH interest_match AS (
    SELECT DISTINCT
        i.id AS interest_id,
        i.name AS interest_name,
        m.id AS match_id
    FROM "match" m
    JOIN "user_details" u ON u.id IN (m.fk_person1_id, m.fk_person2_id)
    JOIN user_interest ui ON ui.fk_user_details_id = u.id
    JOIN interest i ON i.id = ui.fk_interest_id
)
SELECT 
    interest_name AS interest,
    COUNT(match_id) AS related_matches
FROM interest_match
GROUP BY interest_name
ORDER BY related_matches DESC;

-- ==========================================================
-- 14. Raport: Dopasowania zakończone w ostatnich 30 dniach
-- ==========================================================
SELECT 
    m.id AS match_id,
    u1.name || ' ' || u1.surname AS user1,
    u2.name || ' ' || u2.surname AS user2,
    m.date_formed,
    m.date_ended
FROM "match" m
JOIN user_details u1 ON m.fk_person1_id = u1.id
JOIN user_details u2 ON m.fk_person2_id = u2.id
WHERE m.status = 'ended'
  AND m.date_ended >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY m.date_ended DESC;


-- ==========================================================
-- 15. Raport: Użytkownicy, którzy nigdy nie dodali zdjęcia do profilu
-- ==========================================================
SELECT u.id, u.name, u.surname
FROM "user_details" u
WHERE NOT EXISTS (
  SELECT 1 FROM image i WHERE i.fk_user_details_id = u.id
);

-- ==========================================================
-- 16. Raport: Średni czas reakcji na wiadomości w każdej rozmowie
-- ==========================================================
SELECT
  c.id AS conversation_id,
  ROUND(AVG(diff_min), 2) AS avg_response_time_min
FROM (
  SELECT
    m.fk_conversation_id,
    m.fk_sender_id,
    LAG(m.fk_sender_id) OVER (PARTITION BY m.fk_conversation_id ORDER BY m.send_time) AS prev_sender,
    EXTRACT(EPOCH FROM (m.send_time - LAG(m.send_time) OVER (
      PARTITION BY m.fk_conversation_id ORDER BY m.send_time
    )))/60 AS diff_min
  FROM message m
) sub
JOIN conversation c ON c.id = sub.fk_conversation_id
WHERE diff_min IS NOT NULL 
  AND sub.fk_sender_id != sub.prev_sender 
GROUP BY c.id
ORDER BY avg_response_time_min;


-- ==========================================================
-- 17. Raport: Użytkownicy, którzy nigdy nie zostali zablokowani przez innych
-- ==========================================================
SELECT u.id, u.name, u.surname
FROM "user_details" u
LEFT JOIN block b ON b.fk_blocked_user_details_id = u.id
WHERE b.fk_blocked_user_details_id IS NULL;


-- ==========================================================
-- 18. Raport: Średni czas trwania dopasowań w dniach, miesiąc po miesiącu
-- ==========================================================
SELECT 
    DATE_TRUNC('month', date_formed) AS month,
    ROUND(AVG(EXTRACT(EPOCH FROM (COALESCE(date_ended, now()) - date_formed))/86400),2) AS avg_duration_days,
    COUNT(*) AS match_count
FROM "match"
GROUP BY month
ORDER BY month DESC;


-- ==========================================================
-- 19. Raport: Użytkownicy z subskrypcją, którzy nie mają żadnych dopasowań
-- ==========================================================
SELECT u.name, u.surname, sp.name AS subscription_plan
FROM "user_details" u
JOIN subscription s ON u.fk_subscription_id = s.id
JOIN subscription_plan sp ON s.fk_subscription_plan_id = sp.id
WHERE u.id NOT IN (
  SELECT fk_person1_id FROM "match"
  UNION
  SELECT fk_person2_id FROM "match"
);

-- ==========================================================
-- 20. Raport: Analiza dopasowań według zgodności zainteresowań
-- Średnia liczba wspólnych pozytywnych zainteresowań między sparowanymi użytkownikami
-- ==========================================================
SELECT
  ROUND(AVG(COALESCE(shared_count, 0)), 2) AS avg_shared_interests
FROM (
  SELECT m.id AS match_id
  FROM "match" m
) matches
LEFT JOIN (
  SELECT m.id AS match_id, COUNT(*) AS shared_count
  FROM "match" m
  JOIN user_interest ui1 ON ui1.fk_user_details_id = m.fk_person1_id AND ui1.is_positive = TRUE
  JOIN user_interest ui2 ON ui2.fk_user_details_id = m.fk_person2_id AND ui2.is_positive = TRUE
  WHERE ui1.fk_interest_id = ui2.fk_interest_id
  GROUP BY m.id
) shared ON matches.match_id = shared.match_id;

-- Returns 10 next suggestions for selected user to swipe. Takes interest, sex and swipes into account
-- User id, for which the action should be performed, must be entered in first helper query
WITH cu AS (
    SELECT
        ud.id AS user_details_id,
        ud.fk_search_preference_id AS search_pref_id,
        ud.fk_sex_id AS user_sex_id
    FROM user_details ud
    WHERE ud.id = 27010
),
preferred_sexes AS (
    SELECT sps.fk_sex_id
    FROM search_preference_sex sps
    JOIN cu ON sps.fk_search_preference_id = cu.search_pref_id
),
already_swiped AS (
    SELECT fk_swiped_user_details_id
    FROM swipe
    JOIN cu  ON swipe.fk_swiping_user_details_id = cu.user_details_id
),
compatibility AS (
    SELECT
        ud.id AS other_user_id,
        SUM(
            CASE
                WHEN cui.is_positive = ui.is_positive THEN ui.level_of_interest
                ELSE -ui.level_of_interest
            END
        ) AS score_user_to_candidate,
        SUM(
            CASE
                WHEN uip.is_positive = ui_user.is_positive THEN ui_user.level_of_interest
                ELSE -ui_user.level_of_interest
            END
        ) AS score_candidate_to_user,
        COUNT(*) AS shared_interests
    FROM user_details ud
    JOIN user_interest ui ON ui.fk_user_details_id = ud.id
    JOIN user_interest cui ON cui.fk_user_details_id = (SELECT user_details_id FROM cu)
        AND cui.fk_interest_id = ui.fk_interest_id
    JOIN search_preference_interest uip ON uip.fk_search_preference_id = ud.fk_search_preference_id
        AND uip.fk_interest_id = cui.fk_interest_id
    JOIN user_interest ui_user ON ui_user.fk_user_details_id = (SELECT user_details_id FROM cu)
        AND ui_user.fk_interest_id = uip.fk_interest_id
    WHERE ud.id <> (SELECT user_details_id FROM cu)
    GROUP BY ud.id
)
SELECT
    ud.id,
    ud.name,
    ud.surname,
    ud.fk_sex_id,
    c.shared_interests,
    ROUND(((c.score_user_to_candidate + c.score_candidate_to_user)/2)::numeric, 2) AS avg_compatibility,
    ROUND(((c.score_user_to_candidate + c.score_candidate_to_user)/2)::numeric, 2) * c.shared_interests AS weighted_score
FROM user_details ud
JOIN compatibility c ON c.other_user_id = ud.id
WHERE
    ((SELECT COUNT(*) FROM preferred_sexes) = 0 OR ud.fk_sex_id IN (SELECT fk_sex_id FROM preferred_sexes))
    AND (
        (SELECT COUNT(*) FROM search_preference_sex sps WHERE sps.fk_search_preference_id = ud.fk_search_preference_id) = 0
        OR (SELECT user_sex_id FROM cu) IN (
            SELECT fk_sex_id
            FROM search_preference_sex sps
            WHERE sps.fk_search_preference_id = ud.fk_search_preference_id
        )
    )
    AND ud.id NOT IN (SELECT fk_swiped_user_details_id FROM already_swiped)
ORDER BY weighted_score DESC NULLS LAST, avg_compatibility DESC, shared_interests DESC, ud.created_at DESC
LIMIT 10;

-- Last 10 messages in every conversation - horribly written (for index testing purposes)
SELECT m.*
FROM message m
WHERE (
    SELECT COUNT(*)
    FROM message m2
    WHERE m2.fk_conversation_id = m.fk_conversation_id
      AND m2.send_time > m.send_time
) < 10
ORDER BY m.fk_conversation_id, m.send_time DESC;

-- amount of subscriptions with specific max users from subscription plan
select subscription_plan.max_users, Count(subscription.id) as amount_of_subscriptions
from subscription INNER JOIN subscription_plan on subscription.fk_subscription_plan_id = 
subscription_plan.id
Group by subscription_plan.max_users;

-- Active subscriptions where owner's subscription id is different than subscription id
SELECT COUNT(subscription.id)
FROM subscription INNER JOIN user_details ON subscription.fk_owner_id = user_details.id
WHERE user_details.fk_subscription_id IS DISTINCT FROM subscription.id
AND subscription.is_active = true;


