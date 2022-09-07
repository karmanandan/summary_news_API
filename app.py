from flask import Flask
import requests
from sumy.parsers.html import HtmlParser
from sumy.nlp.tokenizers import Tokenizer
import urllib.request
from bs4 import BeautifulSoup
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from string import punctuation
from collections import Counter
from heapq import nlargest


app = Flask(__name__)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
}


def news_api_request(url: str, **kwargs) -> list:
    """
    Sends GET request to News API endpoint

    Inputs
    ----------
    url: full URL for endpoint
    kwargs: please refer to
            News API documentations:
            https://newsapi.org/docs/endpoints/
            (apiKey argument is required)

    Return
    ----------
    list containing data for each article in response
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
    }

    params = kwargs
    res = requests.get(url, params=params, headers=headers)
    articles = res.json().get("articles")
    return articles


def summary_function(text, per=0.10):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    word_frequencies = {}
    for word in doc:
        if word.text.lower() not in list(STOP_WORDS):
            if word.text.lower() not in punctuation:
                if word.text not in word_frequencies.keys():
                    word_frequencies[word.text] = 1
                else:
                    word_frequencies[word.text] += 1

    max_frequency = max(word_frequencies.values())

    for word in word_frequencies.keys():
        word_frequencies[word] = word_frequencies[word] / max_frequency

    sentence_tokens = [sent for sent in doc.sents]
    sentence_scores = {}

    for sent in sentence_tokens:
        for word in sent:
            if word.text.lower() in word_frequencies.keys():
                if sent not in sentence_scores.keys():
                    sentence_scores[sent] = word_frequencies[word.text.lower()]
                else:
                    sentence_scores[sent] += word_frequencies[word.text.lower()]

    select_length = int(len(sentence_tokens) * per)

    summary = nlargest(select_length, sentence_scores, key=sentence_scores.get)

    final_summary = [word.text for word in summary]

    summary = "".join(final_summary)
    return summary

    # doc = nlp(text)
    # keyword = []
    # stopwords = list(STOP_WORDS)
    # pos_tag = ["PROPN", "ADJ", "NOUN", "VERB"]
    # for token in doc:
    #     if token.text in stopwords or token.text in punctuation:
    #         continue
    #     if token.pos_ in pos_tag:
    #         keyword.append(token.text)

    # freq_word = Counter(keyword)
    # max_freq = Counter(keyword).most_common(1)[0][1]
    # for word in freq_word.keys():
    #     freq_word[word] = freq_word[word] / max_freq

    # sent_strength = {}
    # for sent in doc.sents:
    #     for word in sent:
    #         if word.text in freq_word.keys():
    #             if sent in sent_strength.keys():
    #                 sent_strength[sent] += freq_word[word.text]
    #             else:
    #                 sent_strength[sent] = freq_word[word.text]

    # summarized_sentences = nlargest(3, sent_strength, key=sent_strength.get)
    # final_sentences = [w.text for w in summarized_sentences]
    # summary = " ".join(final_sentences)
    # return summary


def read_data_url(url: str) -> str:

    # here we have to pass url and path
    # (where you want to save ur text file)
    # text_file = urllib.request.urlretrieve(url, 'text_file.txt')
    try:
        with urllib.request.urlopen(url) as response:

            contents = response.read()

            soup = BeautifulSoup(contents, "html.parser")

            data_op = ""
            for data in soup.find_all("p"):
                sum = data.get_text()
                data_op += sum
            return summary_function(data_op)

    except Exception as e:
        pass


def get_top_headlines(url: str, sentences_count: int, **kwargs) -> list:

    """
    Sends GET request to News API /v2/top-headlines endpoint,
    and summarizes data at each URL

    Inputs
    ----------
    sentences_count: specifies max number of sentences for return value
    kwargs: see News API
                    documentation:
                    https://newsapi.org/docs/endpoints/top-headlines

    Return
    ----------
    list where each element is a dict containing info
    about a single article
    """

    articles = news_api_request(url, **kwargs)
    titles_ = []
    for n_art in articles:
        result_dict = {}
        result_dict["title"] = n_art["title"]
        result_dict["url"] = n_art["url"]
        result_dict["summary"] = read_data_url(n_art["url"])
        result_dict["image"] = n_art["urlToImage"]

        titles_.append(result_dict)
    return titles_


@app.route("/")
def index():
    url = "https://newsapi.org/v2/top-headlines/"
    API_KEY = "6920553cec3249cdac72c37ad059f684"
    sentences_count = 3
    summaries = get_top_headlines(
        url, sentences_count, apiKey=API_KEY, sortBy="publishedAt", country="us"
    )
    return summaries


if __name__ == "__main__":
    app.debug = True
    app.run()
