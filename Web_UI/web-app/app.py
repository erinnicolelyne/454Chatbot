import os, sys
if sys.path[0] != 0:
    scrpt_path_list = os.getcwd().split("\\")
    root_path = "\\".join(scrpt_path_list[0:-2])
    sys.path.insert(0, root_path)
from Datascraping.Data_Collection import CommentCollection
from flask import Flask, request, render_template

import torch
from transformers import AutoTokenizer, AutoModelForQuestionAnswering
from Testing.classifier import Classifier

name = "mrm8488/bert-small-finetuned-squadv2"

tokenizer = AutoTokenizer.from_pretrained(name,)

model = AutoModelForQuestionAnswering.from_pretrained(name, return_dict=False)
classifier = Classifier()

API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
DEVELOPER_KEY = "AIzaSyBAmYHKpB-g14rlihoODKApxs4CiE0iy9w"

caption_collector = CommentCollection(API_SERVICE_NAME, API_VERSION, DEVELOPER_KEY)

def answer_question(question, answer_text):
    '''
    Takes a `question` string and an `answer` string and tries to identify 
    the words within the `answer` that can answer the question. Prints them out.
    '''
    
    # tokenize the input text and get the corresponding indices
    token_indices = tokenizer.encode(question, answer_text)

    # Search the input_indices for the first instance of the `[SEP]` token.
    sep_index = token_indices.index(tokenizer.sep_token_id)

    seg_one = sep_index + 1

    # The remainders lie in the second segment.
    seg_two = len(token_indices) - seg_one
    
    # Construct the list of 0s and 1s.
    segment_ids = [0]*seg_one + [1]*seg_two

    # get the answer for the question
    start_scores, end_scores = model(torch.tensor([token_indices]), # The tokens representing our input combining question and answer.
                                    token_type_ids=torch.tensor([segment_ids])) # The segment IDs to differentiate question from answer

    # Find the tokens with the highest `start` and `end` scores.
    answer_begin = torch.argmax(start_scores)
    answer_end = torch.argmax(end_scores)

    # Get the string versions of the input tokens.
    indices_tokens = tokenizer.convert_ids_to_tokens(token_indices)
    
    answer = indices_tokens[answer_begin:answer_end+1]
    #remove special tokens
    answer = [word.replace("▁","") if word.startswith("▁") else word for word in answer] #use this when using model "twmkn9/albert-base-v2-squad2"
    answer = " ".join(answer).replace("[CLS]","").replace("[SEP]","").replace(" ##","")
    
    return answer


app = Flask(__name__)

@app.route('/get-captions', methods=["GET", "POST"])
def insertCaptionContext():
    if request.method == "POST":
        videoID = request.form.get("videoID")
        caption = caption_collector.getVideoCaptions(videoID)
        return render_template("index.html", context=caption)
    return render_template("index.html")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        form = request.form
        result = []
        bert_abstract = form['paragraph']
        question = form['question']
        # result.append(form['paragraph'])
        result.append(form['question'])
        isq = classifier.predict_question(question)
        if isq == 1:
            result.append("Question")
            answer, prob = answer_question(question, bert_abstract)
            if answer:
                result.append(answer)
                result.append("Probability")
                result.append(prob)
            else:
                result.append("Model could not generate an answer based on these parameters")
                result.append("Probability")
                result.append(0)
        else:
            sentiment = classifier.get_sentiment(question)
            result.append("Non-Question")
            result.append("")
            result.append("Sentiment")
            result.append(sentiment)
        return render_template("index.html", context=bert_abstract, result = result)
    return render_template("index.html")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)