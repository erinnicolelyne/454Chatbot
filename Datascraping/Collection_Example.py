"""
Example YouTube comment scraping and processing to show how to use the modules. 
"""

from Data_Collection import CommentCollection, DataProcessing

API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
DEVELOPER_KEY = "YOUR KEY HERE"
patrickjmt_channelId = "UCFe6jenM1Bc54qtBsIJGRZQ"

collectionObj = CommentCollection(API_SERVICE_NAME, API_VERSION, DEVELOPER_KEY)
processingObj = DataProcessing()

patrickjmt_data = collectionObj.load_data(patrickjmt_channelId, 20)
comment_frame = patrickjmt_data.loc[:,['videoTitle','textDisplay','likeCount','replyCount']]

for i in comment_frame.index:
    comment_frame.loc[i, 'textDisplay'] = processingObj.preprocess_data(comment_frame.loc[i, 'textDisplay'])

comment_frame.head(100)