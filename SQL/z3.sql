SELECT b.id, b.name, b.surname, b.profile_country, b.profile_city, a.billing_country, a.billing_city FROM (
	SELECT "user".id AS user_id, city.name AS billing_city, country.name AS billing_country, country.id AS country_id FROM "user" 
	INNER JOIN subscription ON "user".fk_subscription_id = subscription.id
	INNER JOIN payment_data ON subscription.fk_payment_data_id = payment_data.id
	INNER JOIN billing_address ON payment_data.fk_billing_address_id = billing_address.id
	INNER JOIN city ON billing_address.fk_city_id = city.id
	INNER JOIN country ON city.fk_country_id = country.id
) AS a INNER JOIN (
	SELECT "user".*, city.name AS profile_city, country.name AS profile_country, country.id AS country_id FROM "user"
	INNER JOIN city ON "user".fk_city_id = city.id
	INNER JOIN country ON city.fk_country_id = country.id
) AS b ON a.user_id = b.id WHERE a.country_id != b.country_id;
