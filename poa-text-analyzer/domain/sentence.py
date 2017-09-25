# encoding: utf-8

import jieba
import codecs

class Sentence:
    SCORE_KEYWORD_NOT_IN_SENTENCE = 0.1
    SCORE_KEYWORD_IN_SENTENCE = 1

    def __init__(self, article_id, raw_sentence):
        self.article_id = article_id
        self.raw_sentence = raw_sentence
        self.negative_word_count = 0
        self.negative_word_score = 0.0
        self.positive_word_count = 0
        self.positive_word_score = 0.0
        self.keyword_count = 0
        self.keyword_score = 0.0
        self.score = 0.0