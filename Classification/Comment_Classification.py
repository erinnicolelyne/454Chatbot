"""
BERT Encoding for a Selection of Comments

Written by: J. Salari and R. Harman
"""

# !rm -rf bert
# !git clone https://github.com/google-research/bert
import sys
sys.path.append('bert/') # for when this folder is added
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import codecs
import collections
import json
import re
import os
import pprint
import numpy as np
import tensorflow as tf
import modeling
import tokenization
from google.colab import auth

class Comment_Classification():

    def __init__(self):
        assert 'COLAB_TPU_ADDR' in os.environ, 'ERROR: Not connected to a TPU runtime; please see the first cell in this notebook for instructions!'
        TPU_ADDRESS = 'grpc://' + os.environ['COLAB_TPU_ADDR']
        print('TPU address is', TPU_ADDRESS)
        auth.authenticate_user()
        with tf.Session(TPU_ADDRESS) as session:
            print('TPU devices:')
            pprint.pprint(session.list_devices())

            # Upload credentials to TPU.
            with open('/content/adc.json', 'r') as f:
                auth_info = json.load(f)
            tf.contrib.cloud.configure_gcs(session, credentials=auth_info)
            # Now credentials are set for all future sessions on this TPU.

            # Available pretrained model checkpoints:
            #   uncased_L-12_H-768_A-12: uncased BERT base model
            #   uncased_L-24_H-1024_A-16: uncased BERT large model
            #   cased_L-12_H-768_A-12: cased BERT large model
            BERT_MODEL = 'uncased_L-12_H-768_A-12'
            BERT_PRETRAINED_DIR = 'gs://cloud-tpu-checkpoints/bert/' + BERT_MODEL
            print('***** BERT pretrained directory: {} *****'.format(BERT_PRETRAINED_DIR))
            # !gsutil ls $BERT_PRETRAINED_DIR

        self.LAYERS = [-1, -2, -3, -4]
        self.NUM_TPU_CORES = 8
        self.MAX_SEQ_LENGTH = 128
        self.BERT_CONFIG = BERT_PRETRAINED_DIR + '/bert_config.json'
        self.CHKPT_DIR = BERT_PRETRAINED_DIR + '/bert_model.ckpt'
        self.VOCAB_FILE = BERT_PRETRAINED_DIR + '/vocab.txt'
        self.INIT_CHECKPOINT = BERT_PRETRAINED_DIR + '/bert_model.ckpt'
        self.BATCH_SIZE = 128