#----------------------------------------
############## LIBRARIES ################
#----------------------------------------
from datetime import datetime, date
from sqlalchemy import create_engine, text
import time
import logging
import os
import sys
from dotenv import find_dotenv, load_dotenv
import requests
from bs4 import BeautifulSoup
import pandas as pd
#----------------------------------------
########## GLOBAL VARIABLES #############
#----------------------------------------
url = 'https://insideairbnb.com/get-the-data/'
csv_types = ['listings', 'reviews'] # types of csv files to gather
city = 'athens' # (in lowercase) to get the data for the city interested in
listings_cols = [
    "id",
    "host_id",
    "host_url",
    "host_name",
    "neighbourhood_cleansed",
    "latitude",
    "longitude",
    "room_type",
    "price",
    "minimum_nights",
    "availability_365",
    "number_of_reviews",
    "last_review",
    "review_scores_rating",
    "license",
    "calculated_host_listings_count",
]
reviews_cols = [
    "listing_id",
    "date",
]
#----------------------------------------
############## FUNCTIONS ################
#----------------------------------------
# test connection with database
#----------------------------------------
def check_connection():
    for i in range(1, 4):
        try:
            with engine.connect():
                return True
        except Exception:
            logging.exception(f"Database test connection attempt {i} failed!")
            time.sleep(5)
    return False
#----------------------------------------
# query database
#----------------------------------------
def query_db(query, connection):
    return connection.execute(query)
#----------------------------------------
# main logic
#----------------------------------------
def main(city, connection):
    link_found = False # boolean for link found
    new_data_available = False # boolean for available new data
    response = requests.get(url)
    if response.status_code == 200:
        html = BeautifulSoup(response.content, 'html.parser') # get the html
        for csv_type in csv_types:
            # count previous rows (stored in the database) -------------------------------------------------------------------------
            result = query_db(text(f"SELECT row_number_{csv_type} FROM airbnb_data_latest_info WHERE last_update = (SELECT MAX(last_update) FROM airbnb_data_latest_info);"), connection) # get the number of rows that were last inserted for each table
            if csv_type == 'listings':
                previous_row_number_listings = result.scalar()
            else:
                previous_row_number_reviews = result.scalar()
            # count current rows ---------------------------------------------------------------------------------------------------
            result = query_db(text(f"SELECT COUNT(*) FROM {csv_type};"), connection) # get the current number of rows for each table
            if csv_type == 'listings':
                current_row_number_listings = result.scalar()
            else:
                current_row_number_reviews = result.scalar()
        # ----------------------------------------------------------------------------------------------------------------------------------------------
        for csv_type in csv_types:
            for a in html.find_all("a", href=True):
                if city in a["href"] and f"{csv_type}.csv.gz" in a["href"]: # to target the specific compressed files
                    link_found = True # there is new data to gather
                    logging.info(f"The link for {csv_type} was found!")
                    csv_url = a["href"]
                    date_string = csv_url.split("/")[6] # extract the date from the link
                    # ----------------------------------------------------------------------------------------------------------------------------------
                    latest_date_web = date.fromisoformat(date_string) # convert latest date from web to valid date object
                    result = query_db(text("SELECT MAX(last_update) FROM airbnb_data_latest_info;"), connection) # get the latest date from the database
                    latest_date_db = result.fetchone()[0]
                    # ----------------------------------------------------------------------------------------------------------------------------------
                    # --- if the latest available date for data from web matches the last inserted date in the database and
                    # --- no mismatches between rows occur in the tables since last insert then the program ends as no newest data is actually available
                    # ----------------------------------------------------------------------------------------------------------------------------------
                    if latest_date_web == latest_date_db and previous_row_number_listings == current_row_number_listings and previous_row_number_reviews == current_row_number_reviews:
                        logging.info('No newest data available!')
                        break
                    else: # get the data
                        new_data_available = True # there is new data available to gather
                        if csv_type == 'listings':
                            columns = listings_cols
                        else:
                            columns = reviews_cols
                        query_db(text(f"DELETE FROM {csv_type};"), connection) # delete everything from the table to start fresh
                        df = pd.read_csv(csv_url, compression="gzip", usecols=columns) # using pandas library to manipulate the data and which columns to be used
                        if csv_type == 'listings':
                            column = 'id'
                        else:
                            df['date'] = pd.to_datetime(df['date'], errors='coerce') # convert values to valid dates
                            dropped_rows = df[df['date'].isna()] # capture rows with invalid dates
                            if len(dropped_rows) > 0:
                                logging.info(f"Invalid date values found for {csv_type}!")
                                logging.info(f"\n{dropped_rows}")
                            df = df.dropna(subset=['date']) # if not valid dates drop those rows
                            column = 'listing_id'
                        df[column] = pd.to_numeric(df[column], errors='coerce') # convert values to valid numeric ids
                        dropped_rows = df[df[column].isna()] # capture rows with invalid numeric ids
                        if len(dropped_rows) > 0:
                            logging.info(f"Invalid {column} values found for {csv_type}!")
                            logging.info(f"\n{dropped_rows}")
                        df = df.dropna(subset=[column]) # if not valid numeric ids drop those rows
                        if csv_type == 'listings':
                            duplicates = df[df.duplicated(keep=False)] # to save the duplicates
                            if len(duplicates) > 0:
                                logging.info(f"Duplicates found for {csv_type}!")
                                logging.info(f"\n{duplicates}")
                            df = df.drop_duplicates() # drop duplicate rows if they do exist for listings
                        df.to_sql(f"{csv_type}", con=connection, if_exists="append", index=False, method="multi", chunksize=10000) # perform the insert
                        logging.info(f"{len(df)} rows successfully inserted into {csv_type} table!")
                        if csv_type == 'listings':
                            listings_rows = len(df) # assign the number of rows inserted for listings to listings_rows variable
                        else:
                            reviews_rows = len(df) # assign the number of rows inserted for reviews to reviews_rows variable
                            # --- using a helper list to insert the below info to airbnb_data_latest_info table
                            helper_list = []
                            info = {'last_update': latest_date_web, 'row_number_listings': listings_rows, 'row_number_reviews': reviews_rows}
                            helper_list.append(info)
                            df = pd.DataFrame(helper_list)
                            df.to_sql("airbnb_data_latest_info", con=connection, if_exists="append", index=False)
                            logging.info(f"The database was updated with the latest date of available data ({latest_date_web})")
            if link_found == False and new_data_available == False:
                logging.info(f"No relevant {csv_type} link was found for the requested city! Process will end")
                break # abort in any iteration
    else:
         raise Exception(f"Request failed with HTTP response status code: {response.status_code}")
#----------------------------------------
#########################################
#----------------------------------------
if __name__ == "__main__":
    # logging--------------------------------
    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s - %(levelname)s - %(message)s",
        handlers = [logging.StreamHandler(sys.stdout)] #logs streamed directly to GitHub Actions console
    )
    connection_string = os.getenv("CONNECTION_STRING")
    if connection_string:
        engine = create_engine(connection_string)
        db_test = check_connection()
        if db_test:
            logging.info('Connection with database was established!')
            try:
                with engine.begin() as connection:
                    main(city, connection)
            except Exception:
                logging.exception('Program ended abnormally!')
                sys.exit(1)
            logging.info('Program ended normally!')
            sys.exit(0)
        else:
            logging.error('Connection with database could not be established! Program ended.')
            sys.exit(1)
    else:
        logging.error('Connection string not found! Program ended.')
        sys.exit(1)
#----------------------------------------