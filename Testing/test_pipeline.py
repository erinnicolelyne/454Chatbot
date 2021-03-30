import numpy as np

from classifier import IsQuestion
from Data_Collection import CommentCollection
from question_answer import answer_question

from nltk.sentiment import SentimentIntensityAnalyzer

sia = SentimentIntensityAnalyzer()
sia.polarity_scores("I really hate this.")

VIDEO_URLS = []
COMMENTS = []
CAPTIONS = []

# Get captions and comments from the list of videos. Comments should be all separate strings.
# Captions should be downloaded and split into 500 word chunks.
# Chunks should never include caption data from multiple videos, cut off before 500 if at the end of the caption, then start again for the next caption.

# Idea: after question answering, compare the comment's video-ID to the video-ID of the caption chunk which answered the question.
# this will give us an idea of where the answers are coming from (i.e. is it always from the associated video or not)

q_classifier = IsQuestion() # Question classifier class.

for comment in COMMENTS:
    isq = q_classifier.predict_question(comment)
        if isq == 1: # Comment is a question.
            best_score = 0 # Tracks the best answer for a specified caption chunk.
            best_chunk = -1 # Tracks the index of the best caption chunk to retrieve the ID afterwards.
            for i in range(np.size(CAPTIONS)):
                answer = answer_question(comment, CAPTIONS[i])
                answer_score = 1 # UPDATE THIS
                if answer_score > best_score: # If current answer probability is higher than the previous best.
                    best_score = answer_score
                    best_chunk = i
                if comment_id == caption_id:
                    #do stuff
                else:
                    #do other stuff
                
        else: # Comment is not a question. It may be useful to put these outputs into an excel sheet for manual evaluation.
            sentiment = sentiment_analysis(comment)
            if sentiment >= positive_threshold:
                #Return a thank you response
            elif sentiment <= negative_threshold:
                #Return the feedback form
            else:
                #Return nothing