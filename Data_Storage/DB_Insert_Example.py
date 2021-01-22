"""
Example dataframe insertion into the MongoDB database
"""

from DB_Interface import DB_Interface
import pandas as pd

password = "NotSoFast"
dbname = "chatbot_training_db"
ex_dict = {'a':1, 'b':2, 'c':3}
example_df = pd.dataFrame(ex_dict)

interface = DB_Interface("mongodb+srv://user-main:"+password+"@cluster-idchannel.k6c0f.mongodb.net/"+dbname+"?retryWrites=true&w=majority")
interface.add_to_db(dbname, example_df)