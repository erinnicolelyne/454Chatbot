"""
Example YouTube caption scraping and processing to show how to use the modules. 
"""

from Data_Collection import CommentCollection, DataProcessing

API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
DEVELOPER_KEY = "AIzaSyBAmYHKpB-g14rlihoODKApxs4CiE0iy9w"
patrickjmt_channelId = "UCFe6jenM1Bc54qtBsIJGRZQ"

video_id = "zhl-Cs1-sG4"

collectionObj = CommentCollection(API_SERVICE_NAME, API_VERSION, DEVELOPER_KEY)
collectionObj.getVideoCaptions(video_id)
# patrickjmt_data = collectionObj.load_captions(patrickjmt_channelId, 1)