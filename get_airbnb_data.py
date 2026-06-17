#----------------------------------------
############## LIBRARIES ################
#----------------------------------------
from datetime import datetime, date
from sqlalchemy import create_engine, text
import time
import random
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
def main(connection):
    response = requests.get(url)
    if response.status_code == 200:
        html = BeautifulSoup(response.content, 'html.parser') # get the html
        city_section = html.find('h2', attrs={"class": None}) # find the first h2 heading with no class, targeting the 'Data Downloads' section
        cities = city_section.find_all_next('h3') # get a list of all the cities in the section
        for city in cities:
            if 'Athens' in str(city): # targeting Athens city
                date_string = str(str(city.find_next('h4')).strip('<h4>')).split('<span>')[0] # get the date substring of the tag, strip the tags and everything else besides the date included
                # -----------------------------------------------------------------------------------------------
                # --- decide what the script should do
                # --- if the latest available date for data from web matches the last inserted date in the database and
                # --- no mismatches between rows occur in the tables since last insert then the program ends as no newest data is actually available
                # -----------------------------------------------------------------------------------------------
                latest_date_web = datetime.strptime(date_string, '%d %B, %Y').date() # convert latest date from web to valid date object
                result = query_db(text("SELECT MAX(last_update) FROM airbnb_data_latest_info;"), connection) # get the latest date from the database
                latest_date_db = result.fetchone()[0]
                # -----------------------------------------------------------------------------------------------
                result = query_db(text("SELECT row_number_listings FROM airbnb_data_latest_info WHERE last_update = (SELECT MAX(last_update) FROM airbnb_data_latest_info);"), connection) # get the number of rows that were last inserted for listings table
                last_row_number_listings = result.scalar()
                result = query_db(text("SELECT row_number_reviews FROM airbnb_data_latest_info WHERE last_update = (SELECT MAX(last_update) FROM airbnb_data_latest_info);"), connection) # get the number of rows that were last inserted for reviews table
                last_row_number_reviews = result.scalar()
                # -----------------------------------------------------------------------------------------------
                result = query_db(text("SELECT COUNT(*) FROM listings;"), connection) # get the current number of rows for listings table
                current_row_number_listings = result.scalar()
                result = query_db(text("SELECT COUNT(*) FROM reviews;"), connection) # get the current number of rows for reviews table
                current_row_number_reviews = result.scalar()
                # -----------------------------------------------------------------------------------------------
                if latest_date_web == latest_date_db and last_row_number_listings == current_row_number_listings and last_row_number_reviews == current_row_number_reviews:
                    logging.info('No newest data available!')
                else: # get the data
                    csv_type = 'listings' # start with listings
                    while True:
                        time.sleep(random.uniform(30, 60)) # sleeps between requests for extra safety
                        # csv link address
                        csv_url = f"https://data.insideairbnb.com/{str(str(str(city).strip('</h3>')).split(', ')[2]).lower()}/{str(str(str(city).strip('</h3>')).split(', ')[1]).lower()}/{str(str(str(city).strip('</h3>')).split(', ')[0]).lower()}/{latest_date_web}/visualisations/{csv_type}.csv"
                        df = pd.read_csv(csv_url) # using pandas library to manipulate the data
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
                            csv_type = 'reviews' # repeat for reviews
                        else: # id all done
                            reviews_rows = len(df) # assign the number of rows inserted for listings to reviews_rows variable
                            # --- using a helper list to insert the below info to airbnb_data_latest_info table
                            helper_list = []
                            info = {'last_update': latest_date_web, 'row_number_listings': listings_rows, 'row_number_reviews': reviews_rows}
                            helper_list.append(info)
                            df = pd.DataFrame(helper_list)
                            df.to_sql("airbnb_data_latest_info", con=connection, if_exists="append", index=False)
                            logging.info(f"The database was updated with the latest date of available data ({latest_date_web})")
                            break # break from while loop and then from for loop and end normally
                break
    else:
         raise Exception(f"Request (url) failed with HTTP response status code: {response.status_code}")
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
                    main(connection)
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