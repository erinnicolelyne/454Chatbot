"""
DB_Interface.py

Regulates and proceduralizes the addition and manipulation of data to be sent to MongoDB and
retrieves data where necessary.
"""

from pymongo import MongoClient
import numpy as np
import pandas as pd

class DB_Interface():

    def __init__(self, uri, database):
        """
        Required to access the DB, DB_URL is of the form \n

        mongodb://[username:password@]host1[:port1][,...hostN[:portN]][/[defaultauthdb][?options]]
        """
        self.client = MongoClient(uri)
        self.databaseObeject = database
        self.qQuantityDict = {"One" : self.client.databaseObject.find_one, 
                              "Any" : self.client.databaseObeject.find}

    def add_to_db(self, dataframe):
        """
        Inserts the provided dataframe into the database whose name is provided.
        """

        data_dict = dataframe.to_dict('dict', 'dict')
        result = self.databaseObeject.insert_one(data_dict)

        print('Inserted dataframe as {}'.format(str(result.inserted_id)))

    def search(self, **args):
        """
        Searches the database for an element or a document of the user's choice

        Parameters
        ----------
        qType : string \n
            Either "Document" for a dictionary/dataframe (takes the first) or "Element" to search the database
            by a specific key. \n
        key : string \n
            If qtype is "Element", a key is needed. \n
        value : integer/float/string \n
            The value of the key you are attempting to search for. \n
        qQuantity : string \n
            The number of dicts/dataframes you wish to pull that match the conditions, valid \n
            instructions are "One" or "Any". \n

        Returns
        -------
        search_dataframes : dict/array of dicts \n
            Returns one or all of the dictionaries meeting the parameters passed.
        """

        qType = args[0]
        key = args[1]
        value = args[2]
        qQuantity = args[3]

        dict_array = np.array([])

        search_func = self.qQuantityDict[qQuantity]
        if qType == "Document":
            dict_array = np.array(search_func())
        elif qType == "Element":
            dict_array = np.array(search_func({key:value}))
        else:
            print("Search must be 'Element' or 'Document'")

        return dict_array

