
# %%

import six
from google.cloud import language
import os
from google.cloud import language_v1

import six
import pandas as pd
import sys
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="auth.json"

#********************************************
def sample_analyze_sentiment(content):
    client = language_v1.LanguageServiceClient()
    response = client.analyze_sentiment(content)
    document = {'type': 'PLAIN_TEXT', 'content': content}
    client.analyze_sentiment(document)
    sentiment = response.document_sentiment
    return sentiment.score, sentiment.magnitude

print(sample_analyze_sentiment('Amazing work!'))
# %%
