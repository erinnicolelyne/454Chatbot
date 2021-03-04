"""
Example YouTube caption scraping and processing to show how to use the modules. 
"""

from Data_Collection import CommentCollection, DataProcessing

PI_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
DEVELOPER_KEY = "AIzaSyAtR9Q_8WjUrLK7s9iqKheVA1PxgXG9c74"
patrickjmt_channelId = "UCFe6jenM1Bc54qtBsIJGRZQ"

collectionObj = CommentCollection(API_SERVICE_NAME, API_VERSION, DEVELOPER_KEY)

patrickjmt_data = collectionObj.load_captions(patrickjmt_channelId, 50)