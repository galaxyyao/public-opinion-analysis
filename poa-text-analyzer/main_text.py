# encoding: utf-8

import codecs
from text_analyzer import do_text_analyze

text = codecs.open('./resources/demo/demo_difficult_003.txt', 'r', 'utf-8').read()

article = do_text_analyze(text)
