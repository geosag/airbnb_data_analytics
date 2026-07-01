-- Select from listings
WITH room_type_stats AS (
    SELECT 
        room_type,
        PERCENTILE_CONT(0.25) WITHIN GROUP (
            ORDER BY CASE WHEN TRIM(REPLACE(price, '$', ' ')) ~ '^-?[0-9]+(\.[0-9]+)?$' THEN TRIM(REPLACE(price, '$', ' '))::NUMERIC(12, 2) ELSE NULL END
        ) AS q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (
            ORDER BY CASE WHEN TRIM(REPLACE(price, '$', ' ')) ~ '^-?[0-9]+(\.[0-9]+)?$' THEN TRIM(REPLACE(price, '$', ' '))::NUMERIC(12, 2) ELSE NULL END
        ) AS q3
    FROM listings
    WHERE (CASE WHEN TRIM(availability_365) ~ '^[0-9]+$' THEN TRIM(availability_365)::INT ELSE 0 END) > 0
    GROUP BY room_type
)
SELECT 
    CAST(l.id AS TEXT) AS id,
    CASE 
        WHEN TRIM(l.host_id) ~ '^[0-9]+$' THEN TRIM(l.host_id)::INT 
        ELSE NULL 
    END AS host_id,
    TRIM(l.host_url) AS host_url,
    TRIM(l.host_name) AS host_name,
    TRIM(l.neighbourhood_cleansed) AS neighbourhood_cleansed,
    CASE 
        WHEN TRIM(l.latitude) ~ '^-?[0-9]+(\.[0-9]+)?$' THEN TRIM(l.latitude)::DOUBLE PRECISION
        ELSE NULL
    END AS latitude,
    CASE 
        WHEN TRIM(l.longitude) ~ '^-?[0-9]+(\.[0-9]+)?$' THEN TRIM(l.longitude)::DOUBLE PRECISION
        ELSE NULL
    END AS longitude,
    TRIM(l.room_type) AS room_type,
    CASE 
        WHEN TRIM(REPLACE(l.price, '$', ' ')) ~ '^-?[0-9]+(\.[0-9]+)?$' THEN TRIM(REPLACE(l.price, '$', ' '))::NUMERIC(12, 2)
        ELSE NULL
    END AS price,
    CASE 
        WHEN TRIM(l.minimum_nights) ~ '^[0-9]+$' THEN TRIM(l.minimum_nights)::INT
        ELSE NULL 
    END AS minimum_nights,
    CASE 
        WHEN TRIM(l.availability_365) ~ '^[0-9]+$' THEN TRIM(l.availability_365)::INT 
        ELSE NULL 
    END AS availability_365,
    CASE 
        WHEN TRIM(l.number_of_reviews) ~ '^[0-9]+$' THEN TRIM(l.number_of_reviews)::INT 
        ELSE NULL 
    END AS number_of_reviews,
    CASE 
        WHEN TRIM(l.last_review) ~ '^\d{4}-\d{2}-\d{2}$' THEN TRIM(l.last_review)::DATE
        ELSE NULL
    END AS last_review,
    CASE 
        WHEN TRIM(l.review_scores_rating) ~ '^-?[0-9]+(\.[0-9]+)?$' THEN TRIM(l.review_scores_rating)::NUMERIC(5, 2)
        ELSE NULL
    END AS review_scores_rating,
    TRIM(l.license) AS license,
    CASE 
        WHEN TRIM(l.calculated_host_listings_count) ~ '^[0-9]+$' AND TRIM(l.calculated_host_listings_count)::INT > 20 THEN 'Commercial/Enterprise Operator'
        WHEN TRIM(l.calculated_host_listings_count) ~ '^[0-9]+$' AND TRIM(l.calculated_host_listings_count)::INT > 5 THEN 'Boutique Property Manager'
        WHEN TRIM(l.calculated_host_listings_count) ~ '^[0-9]+$' AND TRIM(l.calculated_host_listings_count)::INT > 1 THEN 'Small-Scale Multi-Host'
        ELSE 'Individual/Casual'
    END AS host_tier,
    CASE 
        WHEN l.license IS NULL OR TRIM(l.license) = '' THEN 'Invalid'
        WHEN LENGTH(TRIM(l.license)) = 11 AND TRIM(l.license) ~ '^[0-9]+$' THEN 'Valid'
        WHEN LENGTH(TRIM(l.license)) >= 7 AND TRIM(l.license) !~ '^[0-9]+$' AND UPPER(TRIM(l.license)) <> 'EXEMPT' THEN 'Valid'
        WHEN UPPER(TRIM(l.license)) = 'EXEMPT' THEN 'Review Manually'
        ELSE 'Invalid'
    END AS license_validity,
    'https://www.airbnb.com/rooms/' || l.id AS listing_url,
    (rts.q1 - (1.5 * (rts.q3 - rts.q1))) AS stat_lowerbound,
    (rts.q3 + (1.5 * (rts.q3 - rts.q1))) AS stat_upperbound
FROM listings l
LEFT JOIN room_type_stats rts ON l.room_type = rts.room_type;

-- Select from reviews
SELECT * FROM reviews;

-- Select from airbnb_data_latest_info
SELECT * FROM airbnb_data_latest_info;