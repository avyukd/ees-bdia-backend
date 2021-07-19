import pandas as pd
import numpy as np
import requests
import json
import os
import PyPDF2
from nltk import tokenize
import string
import nltk
from nltk.stem.wordnet import WordNetLemmatizer

req_keywords = set(["shall", "must", "will","should","require","include"])
subject_keywords = set(["incumbent","contractor","vendor","quote","proposal","response"])
general_keywords = set(["key","personnel","resume","set-aside","set aside",
              "labor", "category", "time", "materials", "firm", "fixed", "price", "ffp",
               "evaluation","instruction","criteria"])

def cleanup():
    #remove all pdf files in current directory
    print("In Cleanup...")
    for file in os.listdir():
        if file.endswith(".pdf"):
            os.remove(file)
            
def clean_sentence(s):
    s = s.lower()
    s = s.translate(str.maketrans('', '', string.punctuation))
    lmtzr = WordNetLemmatizer()
    lemmatized_sentence = []
    for word in s.split(" "):
        lemmatized_sentence.append(lmtzr.lemmatize(word))
    return set(lemmatized_sentence)
def score_sentence(s):
    return (len(s.intersection(req_keywords)) > 0) * (len(s.intersection(subject_keywords)) > 0) * (len(s.intersection(general_keywords)))

def parse_RFP(file):
    extension = file.split(".")[-1].lower()
    all_sentences = []
    if extension == "pdf":
        pdfFileObj = open(file, 'rb')
        pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
        solicitation_text = []
        for x in range(pdfReader.numPages):
            content = pdfReader.getPage(x).extractText()
            content = ' '.join(content.split())
            solicitation_sentence_tokens = tokenize.sent_tokenize(content)
            for token in solicitation_sentence_tokens:
                all_sentences.append({"pg":x, "original_sentence":token})
    elif extension == "docx" or extension == "doc":
        print("No Word document support. Please convert to PDF and re-try")
        return []
    else:
        print("Unknown file type.")
        return []
    
    df = pd.DataFrame(all_sentences)
    df["clean_sentence"] = df["original_sentence"].apply(clean_sentence)

    df["score"] = df["clean_sentence"].apply(score_sentence)
    df = df.sort_values(by="score",ascending=False)
    return list(df["original_sentence"])