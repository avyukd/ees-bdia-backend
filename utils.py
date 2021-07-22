import pandas as pd
import numpy as np
#import requests
#import json
import os
#import PyPDF2
#from nltk import tokenize
import string
#import nltk
#from nltk.stem.wordnet import WordNetLemmatizer
import textract
import spacy 
from spacy.matcher import Matcher

req_keywords = set(["shall", "must", "will","should","require","include"])
subject_keywords = set(["incumbent","contractor","vendor","quote","proposal","response"])
general_keywords = set(["key","personnel","resume","set-aside","set aside",
              "labor", "category", "time", "materials", "firm", "fixed", "price", "ffp",
               "evaluation","instruction","criteria"])

def cleanup():
    #remove all pdf files in current directory
    print("In Cleanup...")
    for file in os.listdir():
        if file.endswith(".pdf") and file != "test.pdf":
            os.remove(file)
def get_sentences(matches, doc):
    sents = []
    for match_id, start, end in matches:
        matched_span = doc[start:end]
        matched_span_text = matched_span.text
        sent = ' '.join(matched_span.sent.text.split())
        sents.append(sent)
    return sents

def parse_RFP(filepath):
    #create spacy doc
    nlp = spacy.load('en_core_web_sm')
    text = textract.process(filepath).decode("utf-8")
    doc = nlp(text)

    req_matcher = Matcher(nlp.vocab)
    req_patterns = [
        [
            {"LOWER":{"IN":["contractor","quote","vendor","proposal",
            "contractors","quotes","vendors","proposals"
            ]}},
            {"LOWER":{"IN":["must","will","should"]}}
        ],
        [
            {"LOWER":{"IN":["require", "requirement"]}}
        ]
    ]
    req_matcher.add("Requirements",req_patterns)

    personnel_matcher = Matcher(nlp.vocab)
    personnel_patterns = [
    [{"LOWER":{"IN":["contractor","key"]}},
    {"LOWER":{"IN":["personnel", "employee"]}}]
    ]
    personnel_matcher.add("Personnel",personnel_patterns)

    incumbent_matcher = Matcher(nlp.vocab)
    incumbent_patterns = [
        [{"LOWER":{"IN":["incumbent","transition"]}}]
    ]
    incumbent_matcher.add("Incumbent",incumbent_patterns)   
    
    info_matcher = Matcher(nlp.vocab)
    info_patterns = [
        [{"LOWER":{"IN":["officer","specialist","CO","COTR","representative"]}}, {"ENT_TYPE":"PERSON"}],
        [{"LOWER":"by"}, {"ENT_TYPE":"DATE"}],
        [{"LOWER":"criteria"}]
    ]
    info_matcher.add("Info",info_patterns)

    req_matches = req_matcher(doc)
    info_matches = info_matcher(doc)
    personnel_matches = personnel_matcher(doc)
    incumbent_matches = incumbent_matcher(doc)

    #get sentences
    req_sents = get_sentences(req_matches, doc)
    personnel_sents = get_sentences(personnel_matches, doc)
    info_sents = get_sentences(info_matches, doc)
    incumbent_sents = get_sentences(incumbent_matches, doc)

    return {
        "req_sents": req_sents,
        "personnel_sents": personnel_sents,
        "info_sents": info_sents,
        "incumbent_sents": incumbent_sents
    }


'''            
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
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    
    try:
        #not sure this one is right
        nltk.data.find('corpora/wordnet')
    except:    
        nltk.download('wordnet')
    
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
    return list(df["original_sentence"])'''