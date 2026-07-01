CREATE TABLE IF NOT EXISTS listings (
    id                             BIGINT PRIMARY KEY,
    host_id                        TEXT,
    host_url                       TEXT,
    host_name                      TEXT,
    neighbourhood_cleansed         TEXT,
    latitude                       TEXT,
    longitude                      TEXT,
    room_type                      TEXT,
    minimum_nights                 TEXT,
    price                          TEXT,
    availability_365               TEXT,
    number_of_reviews              TEXT,
    last_review                    TEXT,
    review_scores_rating           TEXT,
    license                        TEXT,
    calculated_host_listings_count TEXT
);

CREATE TABLE IF NOT EXISTS reviews (
    listing_id BIGINT,
    date       DATE
);

CREATE TABLE IF NOT EXISTS airbnb_data_latest_info (
    last_update         DATE PRIMARY KEY,
    row_number_listings INTEGER,
    row_number_reviews  INTEGER
);