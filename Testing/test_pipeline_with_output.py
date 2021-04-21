"""
ENPH 454 Testing Script

Enter the video IDs of testing videos in the VIDEO_IDS list. The script will perform the following:
    1) 
    2)
    3)
    ...
"""

def castToList(obj):
    if isinstance(obj, list):
        pass
    else:
        return [obj]

import numpy as np
import pandas as pd

from classifier import Classifier
from Datascraping.Data_Collection import CommentCollection
from question_answer import answer_question

API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
DEVELOPER_KEY = "AIzaSyBAmYHKpB-g14rlihoODKApxs4CiE0iy9w" 
YTURL_PREFIX = 'http://youtube.com/watch?v='

"""
Fill Paramters Here
"""
# only IDs necessary since URLS have a static format
VIDEO_IDS = []
# max comments per video
MAX_COMMENTS = 50
"""
END
"""

# Get captions and comments from the list of videos. Comments should be all separate strings.
# Captions should be downloaded and split into 500 word chunks.
# Chunks should never include caption data from multiple videos, cut off before 500 if at the end of the caption, then start again for the next caption.

# Idea: after question answering, compare the comment's video-ID to the video-ID of the caption chunk which answered the question.
# this will give us an idea of where the answers are coming from (i.e. is it always from the associated video or not)

# Change these to get best results with a static response to positive and negative comments.
positive_threshold = 0.85
negative_threshold = -0.75

####################################
#                                  #
#           Object Calls           #
#                                  #
####################################

classifier = Classifier() # Question classifier class.
YTObj = CommentCollection(API_SERVICE_NAME, API_VERSION, DEVELOPER_KEY) # youtube acess object

####################################
#                                  #
#          Main Code Body          #
#                                  #
####################################

# dataframe for comments and captions with format
"""
---------------
|              | 'commentList' | 'captionList' |
| VIDEO_IDS[0] |    list(...)  |    list(...)  |
                      ...
|VIDEO_IDS[-1] |    list(...)  |    list(...)  | 
"""
cnc_dataframe = pd.DataFrame(columns=['commentList', 'captionList'], index = VIDEO_IDS)
comment_list = []

for video_id in VIDEO_IDS:
    video_comments = YTObj.get_video_comments(order="time", link=YTURL_PREFIX+video_id, part='snippet', videoId=video_id, maxResults=MAX_COMMENTS, textFormat='plainText')
    video_captions = YTObj.getVideoCaptions(video_id)
    for comment_num in range(len(video_comments[0])):
        comment_list.append(video_comments[0][comment_num]['textDisplay'])
    cnc_dataframe.loc[video_id, :] = [comment_list, video_captions]

COMMENTS = cnc_dataframe.loc[:,'commentList'][0]
CAPTIONS = cnc_dataframe.loc[:,'captionList'][0]

print(CAPTIONS)

rows = []
rows2 = []
for comment in COMMENTS:
    isq = classifier.predict_question(comment)
    if isq == 1: # Comment is a question.
        best_prob = 0 # Tracks the best answer for a specified caption chunk.
        best_chunk = -1 # Tracks the index of the best caption chunk to retrieve the ID afterwards.
        for i in range(np.size(CAPTIONS)):
            answer, prob = answer_question(comment, CAPTIONS[i])
            if answer != '':
                if prob > best_prob: # If current answer probability is higher than the previous best.
                    best_prob = prob
                    best_chunk = i
                # if comment_id == caption_id:
                #     #do stuff
                #     pass
                else:
                    #do other stuff
                    pass
            rows.append([comment,isq,answer,prob])
        rows2.append([comment, isq, answer_question(comment, CAPTIONS[best_chunk])[0], answer_question(comment, CAPTIONS[best_chunk])[1]])
    else: # Comment is not a question. It may be useful to put these outputs into an excel sheet for manual evaluation.
        sentiment = classifier.get_sentiment(comment)
        if sentiment['compound'] >= positive_threshold:
            answer = 'Thanks so much you are a great fan!!!' #Return a thank you response
            pass
        elif sentiment['compound'] <= negative_threshold:
            #Return the feedback form
            answer = 'Sorry you are upset we will review your feedback.'
            pass
        else:
            #Return nothing
            answer = ''
            pass

        rows.append([comment, isq, answer, sentiment['compound']])
        rows2.append([comment, isq, answer, sentiment['compound']])
test_output = pd.DataFrame(rows,columns=["Comment","Question","Answer","Score (probability for questions, sentiment score for comments)"])
test_output.to_excel(r'Specify Path', index = False)
test_output2 = pd.DataFrame(rows2,columns=["Comment","Question","Answer","Score (probability for questions, sentiment score for comments)"])
test_output2.to_excel(r'Specify Path', index = False)