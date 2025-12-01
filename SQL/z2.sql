SELECT "user".id, "user".name, "user".surname, a.banned_days, a.number_of_bans FROM (
	SELECT ban.fk_user_id, SUM(ban.period_days) AS "banned_days", COUNT(ban.id) AS "number_of_bans"
	FROM ban 
	GROUP BY ban.fk_user_id 
) AS a
INNER JOIN "user" on a.fk_user_id = "user".id
ORDER BY a.banned_days DESC LIMIT 25;
