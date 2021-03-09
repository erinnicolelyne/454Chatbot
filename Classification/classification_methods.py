# -*- coding: utf-8 -*-
"""classification_draft (1).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/11zaVUOGBQ2V35mAMK3JJGKR9LC2QR0pl
"""

# Loading Packages
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from timeit import default_timer as timer
import pandas as pd
import numpy as np
import requests
import re

from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
import csv
import os
from os.path import exists

"""## Data Ingestion"""

# Secret keys and authorization
CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
DEVELOPER_KEY = "AIzaSyBAmYHKpB-g14rlihoODKApxs4CiE0iy9w"

def get_authenticated_service():
    #flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    #credentials = flow.run_console()
    print("Authenticating")
    return build(API_SERVICE_NAME, API_VERSION, developerKey = DEVELOPER_KEY)

def get_authenticated_service():
    #flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    #credentials = flow.run_console()
    print("Authenticating")
    return build(API_SERVICE_NAME, API_VERSION, developerKey = DEVELOPER_KEY)

def comments_list(service, part, parent_id):
    results = service.comments().list(
    parentId=parent_id,
    part=part
  ).execute()

    return results

def get_video_comments(service, channel_id, videoId, link, **kwargs):
    comments = []

    videoResult = service.videos().list(part='snippet,statistics', id=videoId).execute()
    
    # Getting Video Data
    for itemVideo in videoResult['items']:
        print(itemVideo)
        videoTitle = itemVideo['snippet']['title']
        videoTime = itemVideo['snippet']['publishedAt']
        #totalComments = itemVideo['statistics']['commentCount']
    
    try:
      results = service.commentThreads().list(videoId = videoId, **kwargs).execute()
    except (HttpError):
      return [], videoTitle, videoTime, 1

    # Check if comments are dissabled
    #if totalComments == 0:
    #  print('no comments for video: ' + videoTitle)
    #  return [], videoTitle, videoTime, 1

    # Flags are used for a different implementation that updates data instead of pulling fresh, can be ignored
    firstCommentFlag = 0 #this is a flag to determine if the comment is the first
    no_existing_data_flag = 0 #If no prior data exists do not run reply retrieval

    while results:
        for item in results['items']:
                
            linkToComment = link + item['id'] #Create Comment link
            
            try:
                #Creating the comment dictionary
                comment = {
                    # Video info
                    'videoTitle': videoTitle,
                    'videoTimePosted': videoTime,
                    'videoID': item['snippet']['topLevelComment']['snippet']['videoId'],
                    
                    # Author info
                    'authorDisplayName': item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                    'authorProfileImageUrl': item['snippet']['topLevelComment']['snippet']['authorProfileImageUrl'],
                    'authorChannelUrl':  item['snippet']['topLevelComment']['snippet']['authorChannelUrl'],
                    'authorID': item['snippet']['topLevelComment']['snippet']['authorChannelId']['value'],
                    
                    # Comment Info
                    'commentID': item['snippet']['topLevelComment']['id'],
                    'linkToComment': linkToComment,
                    'textDisplay': item['snippet']['topLevelComment']['snippet']['textDisplay'],
                    'parentID': None,
                    'viewerRating': item['snippet']['topLevelComment']['snippet']['viewerRating'],
                    'likeCount': item['snippet']['topLevelComment']['snippet']['likeCount'],
                    'replyCount': item['snippet']['totalReplyCount'],
                    'publishedAt': item['snippet']['topLevelComment']['snippet']['publishedAt'],
                    'isReply': False
                }

                comments.append(comment)

                # Check if comment contains replies
                replyValue = int(item['snippet']['totalReplyCount'])
                if replyValue > 0:
                    #if it contains replies, pull those replies as a comment type
                    replyThread = comments_list(service, part='id,snippet', parent_id=item['id'])
                    for reply in replyThread['items']:
                        linkToCommentReply = link + reply['id']
                        commentReply = {
                                        # Video info
                                        'videoTitle': videoTitle,
                                        'videoTimePosted': videoTime,
                                        'videoID': item['snippet']['topLevelComment']['snippet']['videoId'],
                                        
                                        # Author info
                                        'authorDisplayName': reply['snippet']['authorDisplayName'],
                                        'authorProfileImageUrl': reply['snippet']['authorProfileImageUrl'],
                                        'authorChannelUrl':  reply['snippet']['authorChannelUrl'],
                                        'authorID': reply['snippet']['authorChannelId']['value'],
                                        
                                        # Comment Info
                                        'commentID': reply['id'],
                                        'linkToComment': linkToCommentReply,
                                        'textDisplay': reply['snippet']['textDisplay'],
                                        'parentID': reply['snippet']['parentId'],
                                        'viewerRating': reply['snippet']['viewerRating'],
                                        'likeCount': reply['snippet']['likeCount'],
                                        'replyCount': None,
                                        'publishedAt': reply['snippet']['publishedAt'],
                                        'isReply': True
                                    }
                        comments.append(commentReply)
            
            except KeyError:
                print(linkToComment)

        # Check if another page exists
        if 'nextPageToken' in results:
            kwargs['pageToken'] = results['nextPageToken']
            try:
                results = service.commentThreads().list(videoId = videoId, **kwargs).execute()
            except:
                break
        else:
            break
    print('wrote')
    return comments, videoTitle, videoTime, no_existing_data_flag

def get_playlist(service, numberVids, **kwargs):
    videoPlaylist = service.channels().list(**kwargs).execute()
    videoListCurrent = []
    
    print("getting playlist")
    for playlists in videoPlaylist['items']:
        uploadID = playlists['contentDetails']['relatedPlaylists']['uploads']
        #print(uploadID)

    
    getVideos = service.playlistItems().list(part="snippet,contentDetails", playlistId = uploadID, maxResults = numberVids).execute()
    #print("getting videos")
    for uploads in getVideos['items']:
        videoGrab = uploads['contentDetails']['videoId']
        videoListCurrent.append(videoGrab)

    print(videoListCurrent)
    return videoListCurrent
    
def load_data(channel_id, numberVids):
    # When running locally, disable OAuthlib's HTTPs verification. When
    # running in production *do not* leave this option enabled.
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    service = get_authenticated_service()


    videoTitle = ""
    videoList = get_playlist(service, numberVids, part="snippet, contentDetails", id=channel_id)

    counter = 0
    final_result = pd.DataFrame()
    for videoId in videoList:

        
        # videos = get_playlist(service, part='snippet', channelId=channelId,maxResults=25, textFormat='plainText')
        # videoId = "3rC76KaH4os"
        maxres = 100
        link = "https://www.youtube.com/watch?v=" + videoId + "&lc="
      
        comments, videoTitle, videoTime, no_existing_data_flag = get_video_comments(service, order="time", channel_id = channel_id, link = link, part='snippet', videoId=videoId, maxResults=maxres, textFormat='plainText')
        final_result = final_result.append(pd.DataFrame(comments), ignore_index=True)

    return final_result

def list_video_titles(load_data_list):
    return load_data_list['videoTitle'][0] 

def removeSpecial(text):
    regrex_pattern = re.compile(pattern = "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags = re.UNICODE)
    return regrex_pattern.sub(r'',text)

patrickjmt_channelId = "UCFe6jenM1Bc54qtBsIJGRZQ"

service = get_authenticated_service()

video_frame = load_data(patrickjmt_channelId, 20)

# #Joey: I added this line to save file to my device, feel free to change path to get your own file

video_frame.to_excel('Video_frame.xlsx', index=False, header=True)

video_frame.head(100)

comment_frame = video_frame.loc[:,['videoTitle','textDisplay','likeCount','replyCount']]

for i in comment_frame.index:
    print(comment_frame.loc[i,'textDisplay']+"\n")

"""## Data PreProcessing"""

! pip install emojis

import emojis
comment_frame.textDisplay = comment_frame.textDisplay.apply(lambda x: emojis.decode(x).replace(':', ' ').replace('_', ' '))

import nltk
nltk.download('stopwords')

# imports
from bs4 import BeautifulSoup
import unicodedata
# from contractions import CONTRACTION_MAP # from contractions.py
import re 
import string
import nltk
import spacy
nlp = spacy.load('en',parse=True,tag=True, entity=True)
from nltk.tokenize import ToktokTokenizer
tokenizer = ToktokTokenizer()
stopword_list = nltk.corpus.stopwords.words('english')
# custom: removing words from list
stopword_list.remove('not')

CONTRACTION_MAP = {
"ain't": "is not",
"aren't": "are not",
"can't": "cannot",
"can't've": "cannot have",
"'cause": "because",
"could've": "could have",
"couldn't": "could not",
"couldn't've": "could not have",
"didn't": "did not",
"doesn't": "does not",
"don't": "do not",
"hadn't": "had not",
"hadn't've": "had not have",
"hasn't": "has not",
"haven't": "have not",
"he'd": "he would",
"he'd've": "he would have",
"he'll": "he will",
"he'll've": "he he will have",
"he's": "he is",
"how'd": "how did",
"how'd'y": "how do you",
"how'll": "how will",
"how's": "how is",
"I'd": "I would",
"I'd've": "I would have",
"I'll": "I will",
"I'll've": "I will have",
"I'm": "I am",
"I've": "I have",
"i'd": "i would",
"i'd've": "i would have",
"i'll": "i will",
"i'll've": "i will have",
"i'm": "i am",
"i've": "i have",
"isn't": "is not",
"it'd": "it would",
"it'd've": "it would have",
"it'll": "it will",
"it'll've": "it will have",
"it's": "it is",
"let's": "let us",
"ma'am": "madam",
"mayn't": "may not",
"might've": "might have",
"mightn't": "might not",
"mightn't've": "might not have",
"must've": "must have",
"mustn't": "must not",
"mustn't've": "must not have",
"needn't": "need not",
"needn't've": "need not have",
"o'clock": "of the clock",
"oughtn't": "ought not",
"oughtn't've": "ought not have",
"shan't": "shall not",
"sha'n't": "shall not",
"shan't've": "shall not have",
"she'd": "she would",
"she'd've": "she would have",
"she'll": "she will",
"she'll've": "she will have",
"she's": "she is",
"should've": "should have",
"shouldn't": "should not",
"shouldn't've": "should not have",
"so've": "so have",
"so's": "so as",
"that'd": "that would",
"that'd've": "that would have",
"that's": "that is",
"there'd": "there would",
"there'd've": "there would have",
"there's": "there is",
"they'd": "they would",
"they'd've": "they would have",
"they'll": "they will",
"they'll've": "they will have",
"they're": "they are",
"they've": "they have",
"to've": "to have",
"wasn't": "was not",
"we'd": "we would",
"we'd've": "we would have",
"we'll": "we will",
"we'll've": "we will have",
"we're": "we are",
"we've": "we have",
"weren't": "were not",
"what'll": "what will",
"what'll've": "what will have",
"what're": "what are",
"what's": "what is",
"what've": "what have",
"when's": "when is",
"when've": "when have",
"where'd": "where did",
"where's": "where is",
"where've": "where have",
"who'll": "who will",
"who'll've": "who will have",
"who's": "who is",
"who've": "who have",
"why's": "why is",
"why've": "why have",
"will've": "will have",
"won't": "will not",
"won't've": "will not have",
"would've": "would have",
"wouldn't": "would not",
"wouldn't've": "would not have",
"y'all": "you all",
"y'all'd": "you all would",
"y'all'd've": "you all would have",
"y'all're": "you all are",
"y'all've": "you all have",
"you'd": "you would",
"you'd've": "you would have",
"you'll": "you will",
"you'll've": "you will have",
"you're": "you are",
"you've": "you have"
}

# function to remove accented characters
def remove_accented_chars(text):
    new_text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8', 'ignore')
    return new_text

# function to expand contractions
def expand_contractions(text, map=CONTRACTION_MAP):
    pattern = re.compile('({})'.format('|'.join(map.keys())), flags=re.IGNORECASE|re.DOTALL)
    def get_match(contraction):
        match = contraction.group(0)
        first_char = match[0]
        expanded = map.get(match) if map.get(match) else map.get(match.lower())
        expanded = first_char+expanded[1:]
        return expanded 
    new_text = pattern.sub(get_match, text)
    new_text = re.sub("'", "", new_text)
    return new_text

# function to remove special characters
def remove_special_characters(text):
    # define the pattern to keep
    pat = r'[^a-zA-z0-9.,!?/:;\"\'\s]' 
    return re.sub(pat, '', text)

# function to remove numbers
def remove_numbers(text):
    # define the pattern to keep
    pattern = r'[^a-zA-z.,!?/:;\"\'\s]' 
    return re.sub(pattern, '', text)

# function to remove punctuation
def remove_punctuation(text):
    text = ''.join([c for c in text if c not in string.punctuation])
    return text

# function for stemming
def get_stem(text):
    stemmer = nltk.porter.PorterStemmer()
    text = ' '.join([stemmer.stem(word) for word in text.split()])
    return text

# function for Lemmatization
def get_lem(text):
    text = nlp(text)
    text = ' '.join([word.lemma_ if word.lemma_ != '-PRON-' else word.text for word in text])
    return text

# function to remove stopwords
def remove_stopwords(text):
    # convert sentence into token of words
    tokens = tokenizer.tokenize(text)
    tokens = [token.strip() for token in tokens]
    # check in lowercase 
    t = [token for token in tokens if token.lower() not in stopword_list]
    text = ' '.join(t)    
    return text

# function to remove whitespaces and tabs
def remove_extra_whitespace_tabs(text):
    #pattern = r'^\s+$|\s+$'
    pattern = r'^\s*|\s\s*'
    return re.sub(pattern, ' ', text).strip()

# function to get lowercase characters
def to_lowercase(text):
    return text.lower()

# Remove HTML Tags
rows = []
for t in comment_frame['textDisplay']:
    soup = BeautifulSoup(t,"lxml")
    rows.append(soup.get_text())
comment_frame['textDisplay'] = rows

comment_frame.textDisplay = comment_frame.textDisplay.apply(lambda x:str(x).replace("’","'"))

for i in comment_frame.index:
    comment_frame.loc[i,'textDisplay'] = expand_contractions(comment_frame.loc[i,'textDisplay'])
    comment_frame.loc[i,'textDisplay'] = remove_accented_chars(comment_frame.loc[i,'textDisplay'])
    comment_frame.loc[i,'textDisplay'] = remove_special_characters(comment_frame.loc[i,'textDisplay'])
    # comment_frame.loc[i,'textDisplay'] = remove_numbers(comment_frame.loc[i,'textDisplay'])
    # comment_frame.loc[i,'textDisplay'] = remove_punctuation(comment_frame.loc[i,'textDisplay'])
    # comment_frame.loc[i,'textDisplay'] = get_stem(comment_frame.loc[i,'textDisplay'])
    # comment_frame.loc[i,'textDisplay'] = get_lem(comment_frame.loc[i,'textDisplay'])
    # comment_frame.loc[i,'textDisplay'] = remove_stopwords(comment_frame.loc[i,'textDisplay'])
    comment_frame.loc[i,'textDisplay'] = remove_extra_whitespace_tabs(comment_frame.loc[i,'textDisplay'])
    comment_frame.loc[i,'textDisplay'] = to_lowercase(comment_frame.loc[i,'textDisplay'])
    print(comment_frame.loc[i,'textDisplay']+"\n")

comment_frame.head(100)

comment_frame.to_excel('Processed Comments.xlsx')

"""## Training

Method 1. Using SKlearn with either multinomial naive bayes or support vector machines.
"""

# install ktrain on Google Colab
# !pip3 install ktrain

video_frame['textDisplay'].to_csv('textDisplay.txt')

pip install pycorenlp

# !apt update -q
# !apt-get install -q openjdk-11-jdk-headless
# !curl -L https://github.com/SpencerPark/IJava/releases/download/v1.3.0/ijava-1.3.0.zip -o ijava-kernel.zip
# !unzip -q ijava-kernel.zip -d ijava-kernel && cd ijava-kernel && python3 install.py --sys-prefix
# !jupyter kernelspec list



import sklearn
import re
from sklearn.svm import SVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn import preprocessing
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix

class IsQuestionAdvanced():
    
    # Init constructor
    # Input: Type of classification: 'MNB' - Multinomial Naive Bayes | 'SVM' - Support Vector Machine
    def __init__(self, classification_type):
        self.classification_type = classification_type
        df = self.__get_data()
        df = self.__clean_data(df)
        df = self.__label_encode(df)
        vectorizer_classifier = self.__create_classifier(df, self.classification_type)
        if vectorizer_classifier is not None:
            self.vectorizer = vectorizer_classifier['vectorizer']
            self.classifier = vectorizer_classifier['classifier']        
        
    # Method (Private):  __clean_data
    # Input: Raw input dataframe
    # Processing: 1. Rename column 
    # 2. lowercase text
    # 3. preserve alpha numeric characters, whitespace, apostrophe
    # 4. filter dataframe with question types - what, who, when, affirmation, unknown
    # Return: Processed filtered dataframe
    def __clean_data(self, df):
        df.rename(columns={0: 'text', 1: 'type'}, inplace=True)
        df['type'] = df['type'].str.strip()
        df['text'] = df['text'].apply(lambda x: x.lower())
        df['text'] = df['text'].apply((lambda x: re.sub('[^a-zA-z0-9\s\']','',x)))
        return df[(df['type'] == 'what') | (df['type'] == 'who') | (df['type'] == 'when') | (df['type'] == 'unknown') | (df['type'] == 'affirmation')]
    

    # Method (Private): __label_encode
    # Input: Processed dataframe
    # Processing: Use label encoding to convert text label to integer label and add it to a new column
    # Return: Processed dataframe with label encoding column
    def __label_encode(self, df):
        self.le = preprocessing.LabelEncoder()
        self.le.fit(df['type'])
        df['label'] = list(self.le.transform(df['type']))
        return df
    
    # Method (Private): __create_classifier
    # Input: 1. Processed dataframe 2. Type of classification
    # Processing: 1. Perform TFIDF Vectorization
    # 2. Appy fit_tranform using TFIDF on text column
    # 3. Split data into 70% training and 30% testing
    # 4. Perform Multinomial Naive Bayes OR SVM classifcation based on input provided
    # 5. Peform prediction for both classification techniques on test data
    # 6. Show confusion matrix and accuracy
    # Return: Dict - TFIDF Vetctorizer, Classifier    
    def __create_classifier(self, df, classification_type):
        v = TfidfVectorizer(analyzer='word',lowercase=True)
        X = v.fit_transform(df['text'])
        X_train, X_test, y_train, y_test = train_test_split(X, df['label'], test_size=0.30)
        if classification_type == 'MNB':
            clf = MultinomialNB()
            clf.fit(X_train,y_train)
            preds = clf.predict(X_test)
            print(classification_report(preds,y_test))
            print('Accuracy is: ', clf.score(X_test,y_test))
            return {'vectorizer': v, 'classifier': clf}
        elif classification_type == 'SVM':
            clf_svm = SVC(kernel='linear')
            clf_svm.fit(X_train,y_train)
            preds = clf_svm.predict(X_test)
            preds = print(classification_report(preds,y_test))
            print('Accuracy is: ', clf_svm.score(X_test,y_test))
            return {'vectorizer': v, 'classifier': clf_svm}
        else:
            print("Wrong classification type: \n Type 'MNB' - Multinomial Naive Bayes \n Type 'SVM' - Support Vector Machine")    
            

    # Method (Private): __get_data
    # Processing: Get the sample input data used to create traning, test, vectorizer, classifier data
    # Return: Pandas dataframe
    def __get_data(self):
        return pd.read_csv('sample.txt', sep=',,,', header=None)
    
    # Method (Public): predict
    # Input: An unknown new sentence
    # Return: Prediction - Typpe of question 'what', 'when', 'who'
    def predict(self, sentence):
        ex = self.vectorizer.transform([sentence])
        return list(self.le.inverse_transform(self.classifier.predict(ex)))[0]


obj = IsQuestionAdvanced('MNB')

# Run on output of first method
# df_method1_out = pd.read_csv('output/method1_output.csv')
# df_method1_out = df_method1_out[df_method1_out['is_question'] == 1]
# df_method1_out['question_type'] = df_method1_out['QUERY'].apply(obj.predict)
# df_method1_out.to_csv('output/method3_output_1.csv', index=False)

# # Run on output of first method
# df_method2_out = pd.read_csv('output/method2_output.csv')
# del df_method2_out['question_type']
# df_method2_out = df_method2_out[df_method2_out['is_question'] == 1]
# df_method2_out['question_type'] = df_method2_out['QUERY'].apply(obj.predict)
# df_method2_out.to_csv('output/method3_output_2.csv', index=False)

testData = pd.read_csv('textDisplay.csv')
testData['question_type'] = testData['textDisplay'].apply(obj.predict)

testData.to_excel('Classified Comments.xlsx')

testData

"""Method 2. Using nltk multinomial naive bayes."""

import nltk
nltk.download('nps_chat')
nltk.download('punkt')

import re
import nltk.corpus
from nltk.corpus import nps_chat
import pandas as pd

class IsQuestion():
    
    # Init constructor
    def __init__(self):
        posts = self.__get_posts()
        feature_set = self.__get_feature_set(posts)
        self.classifier = self.__perform_classification(feature_set)
        
    # Method (Private): __get_posts
    # Input: None
    # Output: Posts (Text) from NLTK's nps_chat package
    def __get_posts(self):
        return nltk.corpus.nps_chat.xml_posts()
    
    # Method (Private): __get_feature_set
    # Input: Posts from NLTK's nps_chat package
    # Processing: 1. preserve alpha numeric characters, whitespace, apostrophe
    # 2. Tokenize sentences using NLTK's word_tokenize
    # 3. Create a dictionary of list of tuples for each post where tuples index 0 is the dictionary of words occuring in the sentence and index 1 is the class as received from nps_chat package 
    # Return: List of tuples for each post
    def __get_feature_set(self, posts):
        feature_list = []
        for post in posts:
            post_text = post.text            
            features = {}
            words = nltk.word_tokenize(post_text)
            for word in words:
                features['contains({})'.format(word.lower())] = True
            feature_list.append((features, post.get('class')))
        return feature_list
    
    # Method (Private): __perform_classification
    # Input: List of tuples for each post
    # Processing: 1. Divide data into 80% training and 10% testing sets
    # 2. Use NLTK's Multinomial Naive Bayes to perform classifcation
    # 3. Print the Accuracy of the model
    # Return: Classifier object
    def __perform_classification(self, feature_set):
        training_size = int(len(feature_set) * 0.1)
        train_set, test_set = feature_set[training_size:], feature_set[:training_size]
        classifier = nltk.NaiveBayesClassifier.train(train_set)
        print('Accuracy is : ', nltk.classify.accuracy(classifier, test_set))
        return classifier
        
    # Method (private): __get_question_words_set
    # Input: None
    # Return: Set of commonly occuring words in questions
    def __get_question_words_set(self):
        question_word_list = ['what', 'where', 'when','how','why','did','do','does','have','has','am','is','are','can','could','may','would','will','should'
"didn't","doesn't","haven't","isn't","aren't","can't","couldn't","wouldn't","won't","shouldn't",'?']
        return set(question_word_list)        
    
    # Method (Public): predict_question
    # Input: Sentence to be predicted
    # Return: 1 - If sentence is question | 0 - If sentence is not question
    def predict_question(self, text):
        words = nltk.word_tokenize(text.lower())        
        if self.__get_question_words_set().intersection(words) == False:
            return 0
        if '?' in text:
            return 1
        
        features = {}
        for word in words:
            features['contains({})'.format(word.lower())] = True            
        
        prediction_result = self.classifier.classify(features)
        if prediction_result == 'whQuestion' or prediction_result == 'ynQuestion':
            return 1
        return 0
    
    # Method (Public): predict_question_type
    # Input: Sentence to be predicted
    # Return: 'WH' - If question is WH question | 'YN' - If sentence is Yes/NO question | 'unknown' - If unknown question type
    def predict_question_type(self, text):
        words = nltk.word_tokenize(text.lower())                
        features = {}
        for word in words:
            features['contains({})'.format(word.lower())] = True            
        
        prediction_result = self.classifier.classify(features)
        if prediction_result == 'whQuestion':
            return 'WH'
        elif prediction_result == 'ynQuestion':
            return 'YN'
        else:
            return 'unknown'


isQ = IsQuestion()
df_1 = pd.read_csv('queries-10k-txt', sep='\t')
df_1['is_question'] = df_1['QUERY'].apply(isQ.predict_question)
df_1['question_type'] = df_1[df_1['is_question'] == 1]['QUERY'].apply(isQ.predict_question_type)
# df_1.to_csv('output/method2_output.csv', index=False)

# df_1.to_excel('Classified Comments_Method2.xlsx')

isQ = IsQuestion()
df_1 = pd.read_csv('textDisplay.csv')
df_1['is_question'] = df_1['textDisplay'].apply(isQ.predict_question)
df_1['question_type'] = df_1[df_1['is_question'] == 1]['textDisplay'].apply(isQ.predict_question_type)

df_1.to_excel('Classified Comments_Method2_test.xlsx')
