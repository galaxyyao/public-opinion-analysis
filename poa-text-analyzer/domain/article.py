# encoding: utf-8
import uuid
import re
import yaml
import redis
import jieba
import math


class Article:
    def __init__(self, raw_article_text):
        self.raw_article_text = raw_article_text
        self.total_score = 0.0
        self.sentences = []
        self.article_id = str(uuid.uuid1())
        self.sentence_score_gt1_count = 0
        self.length_score = 0.0
        self.keywords = []

    def split_into_sentences(self, text):
        paragraphs = str.splitlines(text)
        raw_sentences = []
        for paragraph in paragraphs:
            raw_split_results = re.split(r' *[\。\?!？！][\'"\)\]]* *', paragraph)
            for raw_split_result in raw_split_results:
                if (raw_split_result.rstrip().strip() == ""):
                    continue
                raw_sentences.append(raw_split_result.rstrip().strip())
        return raw_sentences

    def cache_raw_seg(self):
        config = yaml.safe_load(open("./application.yml"))
        r = redis.StrictRedis(host=config['redis']['host'], port=config['redis']['port'], db=config['redis']['db'])
        for i in range(0, len(self.sentences)):
            raw_word_seg_list = jieba.cut_for_search(self.sentences[i].raw_sentence)
            sentence_seg_id = 'article:' + self.article_id + ':raw_seg:' + str(i)
            for raw_word_seg in raw_word_seg_list:
                r.sadd(sentence_seg_id, raw_word_seg)

    def generate_sentence_brief(self):
        config = yaml.safe_load(open("./application.yml"))
        r = redis.StrictRedis(host=config['redis']['host'], port=config['redis']['port'], db=config['redis']['db'])
        for i in range(0, len(self.sentences)):
            sentence_seg_id = 'article:' + self.article_id + ':raw_seg:' + str(i)
            diffs = r.sdiff(sentence_seg_id, 'dict_stopword')
            brief_seg_id = 'article:' + self.article_id + ':brief:' + str(i)
            for diff in diffs:
                if (diff.decode('utf-8').strip() != ""):
                    r.sadd(brief_seg_id, diff.decode('utf-8'))

    def generate_sentence_score(self):
        config = yaml.safe_load(open("./application.yml"))
        r = redis.StrictRedis(host=config['redis']['host'], port=config['redis']['port'], db=config['redis']['db'])
        article_seg_id = 'article:' + self.article_id + ":article_keyword"
        for i in range(0, len(self.sentences)):
            brief_seg_id = 'article:' + self.article_id + ':brief:' + str(i)
            r.sunion(article_seg_id, brief_seg_id)
            # negative
            negative_inter = r.sinter(brief_seg_id, 'dict_negative')
            self.sentences[i].negative_count = len(negative_inter)
            self.sentences[i].negative_score = self.sentences[i].negative_count
            negative_words = ""
            for negative_word in negative_inter:
                negative_words += negative_word.decode('utf-8') + ","

            # positive
            positive_inter = r.sinter(brief_seg_id, 'dict_positive')
            self.sentences[i].positive_count = len(positive_inter)
            self.sentences[i].positive_score = 1 / math.sqrt(math.exp(self.sentences[i].positive_count))

            # keyword
            keyword_inter = r.sinter(brief_seg_id, 'dict_keyword')
            for keyword in keyword_inter:
                if (keyword.decode('utf-8') not in self.keywords):
                    self.keywords.append(keyword.decode('utf-8'))
            self.sentences[i].keyword_count = len(keyword_inter)
            if (self.sentences[i].keyword_count > 0):
                self.sentences[i].keyword_score = 1
            else:
                self.sentences[i].keyword_score = 0.1

            self.sentences[i].score = self.sentences[i].negative_score * self.sentences[i].positive_score * \
                                      self.sentences[i].keyword_score

            print(self.sentences[i].raw_sentence)
            print("Sentence score:" + str(self.sentences[i].score) + \
                  ", negative count:" + str(self.sentences[i].negative_count) + \
                  ", positive count:" + str(self.sentences[i].positive_count) + \
                  ", keyword count:" + str(self.sentences[i].keyword_count) + \
                  ", negative score:" + str(self.sentences[i].negative_score) + \
                  ", positive score:" + str(self.sentences[i].positive_score) + \
                  ", keyword score:" + str(self.sentences[i].keyword_score))
            print('Negative words:' + negative_words)

    def generate_article_score(self):
        total_sentence_score = 0.0
        for i in range(0, len(self.sentences)):
            total_sentence_score += self.sentences[i].score
            if (self.sentences[i].score > 1):
                self.sentence_score_gt1_count += 1

        article_keyword_score = math.sqrt(len(self.keywords))
        self.length_score = (self.sentence_score_gt1_count * article_keyword_score + 1) / math.log2(len(self.sentences))
        print('Origin score:' + str(total_sentence_score) + \
              ", length score:" + str(self.length_score) + \
              ", article keyword score:" + str(article_keyword_score)
              )
        self.total_score = math.atan(total_sentence_score * self.length_score) * 2 / math.pi

    def clean_up_cache(self):
        config = yaml.safe_load(open("./application.yml"))
        r = redis.StrictRedis(host=config['redis']['host'], port=config['redis']['port'], db=config['redis']['db'])
        for key in r.scan_iter("article:" + self.article_id + "*"):
            r.delete(key)
