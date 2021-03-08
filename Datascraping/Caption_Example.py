"""
Example YouTube caption scraping and processing to show how to use the modules. 
"""

from Data_Collection import CommentCollection, DataProcessing

API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
DEVELOPER_KEY = "AIzaSyBAmYHKpB-g14rlihoODKApxs4CiE0iy9w"
patrickjmt_channelId = "UCFe6jenM1Bc54qtBsIJGRZQ"

collectionObj = CommentCollection(API_SERVICE_NAME, API_VERSION, DEVELOPER_KEY, session_type="oauth2")

patrickjmt_data = collectionObj.load_captions(patrickjmt_channelId, 1)