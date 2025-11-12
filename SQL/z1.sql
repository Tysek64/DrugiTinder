\set countryName '''Poland'''
SELECT "user".id, "user".name, "user".surname, city.name, country.name FROM "user" INNER JOIN city ON "user".fk_city_id = city.id INNER JOIN country ON city.fk_country_id = country.id WHERE country.name = :countryName;
