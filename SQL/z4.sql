SELECT every_image.year, every_image.total_images, current_image.number_of_images FROM (
	SELECT date_part('year', uploaded_at) AS year, COUNT(id) AS number_of_images FROM image 
	WHERE is_current 
	GROUP BY date_part('year', uploaded_at)
	ORDER BY date_part('year', uploaded_at) ASC
) AS current_image RIGHT JOIN (
	SELECT date_part('year', uploaded_at) AS year, COUNT(id) AS total_images FROM image 
	GROUP BY date_part('year', uploaded_at)
	ORDER BY date_part('year', uploaded_at) ASC
) AS every_image ON current_image.year = every_image.year;
