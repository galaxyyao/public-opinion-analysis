# encoding: utf-8

import redis
import yaml

config = yaml.safe_load(open("./application.yml"))
r = redis.StrictRedis(host=config['redis']['host'], port=config['redis']['port'], db=config['redis']['db'])
for key in r.scan_iter("article:*"):
    r.delete(key)

for key in r.scan_iter("dict_*"):
    r.delete(key)

