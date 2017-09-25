# encoding: utf-8
import redis
import codecs
import yaml
import jieba
import domain.article
import domain.sentence

def do_text_analyze(text):
    load_dictionary_to_cache()
    jieba.load_userdict("./resources/dict_terminology.txt")

    article = domain.article.Article(text)
    raw_sentences = article.split_into_sentences(text)
    for raw_sentence in raw_sentences:
        sentence = domain.sentence.Sentence(article.article_id, raw_sentence)
        article.sentences.append(sentence)

    article.cache_raw_seg()
    article.generate_sentence_brief()
    article.generate_sentence_score()
    article.generate_article_score()
    print("Article total score:" + str(article.total_score))
    article.clean_up_cache()
    return article


def load_dictionary_to_cache():
    print("Start loading word dictionaries to cache.")
    config = yaml.safe_load(open("./application.yml"))
    r = redis.StrictRedis(host=config['redis']['host'], port=config['redis']['port'], db=config['redis']['db'])

    cache_dict('dict_negative', r)
    cache_dict('dict_positive', r)
    cache_dict('dict_keyword', r)
    cache_dict('dict_stopword', r)


def cache_dict(dict_name, r):
    is_dict_exists = r.keys(dict_name)
    if (len(is_dict_exists) == 0):
        print('Caching dict:' + dict_name)
        words = codecs.open('./resources/' + dict_name + '.txt', 'r', 'utf-8').read().splitlines()
        for word in words:
            r.sadd(dict_name, word)
