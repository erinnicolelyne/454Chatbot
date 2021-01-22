"""
DB_Interface.py

Regulates and proceduralizes the addition and manipulation of data to be sent to MongoDB and
retrieves data where necessary.
"""

from pymongo import MongoClient
import pandas as pd

class DB_Interface():

    def __init__(self, uri):
        """
        Required to access the DB, DB_URL is of the form \n

        mongodb://[username:password@]host1[:port1][,...hostN[:portN]][/[defaultauthdb][?options]]
        """
        self.client = MongoClient(uri)

    def add_to_db(self, database, dataframe):
        """
        Inserts the provided dataframe into the database whose name is provided.
        """

        db = self.client.database

        data_dict = dataframe.to_dict('dict', 'dict')
        result = db.insert_one(data_dict)

        print('Inserted dataframe as {}'.format(str(result.inserted_id)))