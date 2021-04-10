"""
Comment Data-Scraping Module

Written by: J. Salari, R. Harman and Duncan

Uses the google requests API to interact with YouTube and pull comments from
specified videos.
"""

# Loading Packages
import googleapiclient.discovery 
from googleapiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaIoBaseDownload
from timeit import default_timer as timer
import pandas as pd
import numpy as np
import requests
import re
from datetime import datetime, timedelta
import csv
import os
from os.path import exists
from bs4 import BeautifulSoup
import unicodedata
import re 
import string
import nltk
import spacy
import emojis
import io
from pytube import YouTube

class CommentCollection():
    """
    Uses the Google API class to collect comments from YouTube
    """
    def __init__(self, service_name, API_ver, developer_key, session_type="API_Key"):
        """
        service_name = 'youtube'
        API_ver = 'v3'
        developer_key = your individual key to access the Google API
        """
        self.N_MAX = 500
        self.SERVICE = service_name
        self.VER = API_ver
        self.DEV_KEY = developer_key
        if session_type == "OAuth2":
          self.API_BUILD = self.oauth_build_session()
        if session_type == "API_Key":
          self.API_BUILD = googleapiclient.discovery.build(self.SERVICE, self.VER, developerKey = self.DEV_KEY)

    def get_authenticated_service(self):
        """
        Required to access some of the functions of the Google API, depends on scope.
        """
        print("Authenticating")
        return googleapiclient.discovery.build(self.SERVICE, self.VER, developerKey = self.DEV_KEY)

    def oauth_build_session(self):
        flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file="client_secrets.json", scopes=["https://www.googleapis.com/auth/youtube.force-ssl",])

        flow.run_local_server()
        return flow.authorized_session()

    def comments_list(self, part, parent_id):
        """
        Grabs the comments from the parent video
        """
        results = self.API_BUILD.comments().list(
            parentId = parent_id,
            part = part
        ).execute()

        return results

    def captions_list(self, videoId):
        """
        Grabs the captions from the parent video as caption OBJ
        """
        captions_list = self.API_BUILD.captions().list(part = "snippet", videoId = videoId).execute()
        return captions_list

    def get_video_comments(self, videoId, link, **kwargs):
        comments = []

        videoResult = self.API_BUILD.videos().list(part='snippet,statistics', id=videoId).execute()
        print(videoResult)

        # Getting Video Data
        for itemVideo in videoResult['items']:
            print(itemVideo)
            videoTitle = itemVideo['snippet']['title']
            videoTime = itemVideo['snippet']['publishedAt']
            totalComments = itemVideo['statistics']['commentCount']
        
        try:
            results = self.API_BUILD.commentThreads().list(videoId = videoId, **kwargs).execute()
        except (HttpError):
            return [], videoTitle, videoTime, 1

        # Check if comments are disabled
        if totalComments == 0:
         print('no comments for video: ' + videoTitle)
         return [], videoTitle, videoTime, 1

        # Flags are used for a different implementation that updates data instead of pulling fresh, can be ignored
        no_existing_data_flag = 0 # If no prior data exists do not run reply retrieval

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
                        replyThread = self.comments_list(part='id,snippet', parent_id=item['id'])
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
                    results = self.API_BUILD.commentThreads().list(videoId = videoId, **kwargs).execute()
                except:
                    break
            else:
                break
        print('wrote') 
        return comments, videoTitle, videoTime, no_existing_data_flag

    def get_playlist(self, numberVids, **kwargs):
        videoPlaylist = self.API_BUILD.channels().list(**kwargs).execute()
        videoListCurrent = []
        
        print("getting playlist")
        for playlists in videoPlaylist['items']:
            uploadID = playlists['contentDetails']['relatedPlaylists']['uploads']
            #print(uploadID)
        getVideos = self.API_BUILD.playlistItems().list(part="snippet,contentDetails", playlistId = uploadID, maxResults = numberVids).execute()
        #print("getting videos")
        for uploads in getVideos['items']:
            videoGrab = uploads['contentDetails']['videoId']
            videoListCurrent.append(videoGrab)
        return videoListCurrent
        
    def load_data(self, channel_id, numberVids):
        # When running locally, disable OAuthlib's HTTPs verification. When
        # running in production *do not* leave this option enabled.
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        service = self.get_authenticated_service()
        videoList = self.get_playlist(numberVids, part="snippet, contentDetails", id=channel_id)
        final_result = pd.DataFrame()
        for videoId in videoList:
            maxres = 100
            link = "https://www.youtube.com/watch?v=" + videoId + "&lc="
        
            comments, videoTitle, videoTime, no_existing_data_flag = self.get_video_comments(order="time", link = link, part='snippet', videoId=videoId, maxResults=maxres, textFormat='plainText')
            final_result = final_result.append(pd.DataFrame(comments), ignore_index=True)

        return final_result

    def getVideoCaptions(self, video_id, as_chunks=False):
        """
        Gets the captions for a video and returns either the first self.N_MAX if as_chunks = False
        or a list divided into self.N_MAX length strings with the excess appended as the final element
        """
        videoStr = 'http://youtube.com/watch?v=' + str(video_id)
        source = YouTube(videoStr)
        if source.captions.get_by_language_code('a.en') != None:
          en_caption = source.captions.get_by_language_code('a.en')
        elif source.captions.get_by_language_code('en') != None:
          en_caption = source.captions.get_by_language_code('en')
        else:
          print("Unable to generate captions, check the video ID and if it has any captions in the language you are trying to generate for.")
          return
        en_caption_convert_to_srt = en_caption.generate_srt_captions()
        sentences_only = [line for line in en_caption_convert_to_srt.split('\n') if line.strip() != '' and any(c.isalpha() for c in line) == True]
        single_string = " ".join(sentences_only)
        if len(single_string.split(" ")) <= self.N_MAX:
          return single_string
        elif len(single_string.split(" ")) > self.N_MAX and as_chunks == False:
          print("Captions longer than {} words, returning first {} words.".format(self.N_MAX, self.N_MAX))
          return " ".join(single_string.split(" ")[0:self.N_MAX-1])
        elif len(single_string.split(" ")) > self.N_MAX and as_chunks == True:
          chunk_string_list = []
          list_by_word = single_string.split(" ")
          n_words = len(list_by_word)
          n_chunks = n_words // self.N_MAX
          for n in range(n_chunks):
            chunk_string_list.append(" ".join(list_by_word[n*(self.N_MAX):(n+1)*self.N_MAX - 1]))
          chunk_string_list.append(" ".join(list_by_word[n_chunks*self.N_MAX-1: -1]))
          return chunk_string_list

    def load_captions(self, channel_id, numberVids):
      os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
      service = self.get_authenticated_service()
      videoList = self.get_playlist(numberVids, part="snippet, contentDetails", id=channel_id)
      filename = "Captions_" + str(channel_id) + "_" + str(numberVids) + ".txt"
      text_file = open(filename, "w")
      for videoId in videoList:
        videoStr = 'http://youtube.com/watch?v=' + str(videoId)
        source = YouTube(videoStr)
        if source.captions.get_by_language_code('a.en') != None:
          en_caption = source.captions.get_by_language_code('a.en')
        elif source.captions.get_by_language_code('en') != None:
          en_caption = source.captions.get_by_language_code('en')
        else:
          print("Unable to generate captions, check the video ID and if it has any captions in the language you are trying to generate for.")
          return
        en_caption_convert_to_srt = en_caption.generate_srt_captions()
        sentences_only = [line for line in en_caption_convert_to_srt.split('\n') if line.strip() != '' and any(c.isalpha() for c in line) == True]
        for line in sentences_only:
          text_file.write(line)
          text_file.write('\n')
      text_file.close()

    def list_video_titles(self, load_data_list):
        return load_data_list['videoTitle'][0] 

class DataProcessing():
    def __init__(self):
        self.CONTRACTION_MAP = {
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
        self.nlp = spacy.load('en', parse=True, tag=True, entity=True)
        self.tokenizer = nltk.tokenize.ToktokTokenizer()
        self.STOPWORD_LIST = nltk.corpus.stopwords.words('english')
        self.STOPWORD_LIST.remove('not')

    def remove_special_characters(self, text):
        # define the pattern to keep
        pat = r'[^a-zA-z0-9.,!?/:;\"\'\s]' 
        return re.sub(pat, '', text)
    
    def remove_numbers(self, text):
        # define the pattern to keep
        pattern = r'[^a-zA-z.,!?/:;\"\'\s]' 
        return re.sub(pattern, '', text)

    def remove_punctuation(self, text):
        text = ''.join([c for c in text if c not in string.punctuation])
        return text

    def get_stem(self, text):
        stemmer = nltk.porter.PorterStemmer()
        text = ' '.join([stemmer.stem(word) for word in text.split()])
        return text

    def get_lem(self, text):
        text = nlp(text)
        text = ' '.join([word.lemma_ if word.lemma_ != '-PRON-' else word.text for word in text])
        return text

    def remove_stopwords(self, text):
        # convert sentence into token of words
        tokens = self.tokenizer.tokenize(text)
        tokens = [token.strip() for token in tokens]
        # check in lowercase 
        t = [token for token in tokens if token.lower() not in self.STOPWORD_LIST]
        text = ' '.join(t)    
        return text

    def remove_extra_whitespace_tabs(self, text):
        pattern = r'^\s*|\s\s*'
        return re.sub(pattern, ' ', text).strip()

    def remove_accented_chars(self, text):
        new_text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8', 'ignore')
        return new_text

    def expand_contractions(self, text, mapIndex = None):
        if mapIndex == None: 
            mapIndex = self.CONTRACTION_MAP
        pattern = re.compile('({})'.format('|'.join(mapIndex.keys())), flags = re.IGNORECASE|re.DOTALL)
        def get_match(contraction):
            match = contraction.group(0)
            first_char = match[0]
            expanded = mapIndex.get(match) if mapIndex.get(match) else mapIndex.get(match.lower())
            expanded = first_char + expanded[1:]
            return expanded 
        new_text = pattern.sub(get_match, text)
        new_text = re.sub("'", "", new_text)
        return new_text

    def demojify(self, text):
        text = text.apply(lambda x: emojis.decode(x).replace(':', ' ').replace('_', ' '))

    def remove_min_req(self, text, min_characters):
        if len(text) <= min_characters:
            return 
        else:
            return text

    def preprocess_data(self, text, min_characters):
        """
        This function calls all the others to perform the pre-processing on a string
        """
        text = self.demojify(text)
        text = self.expand_contractions(text)
        text = self.remove_accented_chars(text)
        text = self.remove_special_characters(text)
        text = self.remove_numbers(text)
        text = self.remove_punctuation(text)
        text = self.get_lem(text)
        text = self.remove_stopwords(text)
        text = self.remove_extra_whitespace_tabs(text)
        text = text.lower()
        text = self.remove_min_req(text, min_characters)
        text = BeautifulSoup(text,"lxml").get_text()

        return text