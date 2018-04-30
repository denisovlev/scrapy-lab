# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import os
from elasticsearch import Elasticsearch
from dotenv import load_dotenv, find_dotenv
import uuid

class ImdbPipeline(object):

    def __init__(self):
        load_dotenv(find_dotenv())

        ELASTIC_API_URL_HOST = os.environ['ELASTIC_API_URL_HOST']
        ELASTIC_API_URL_PORT = os.environ['ELASTIC_API_URL_PORT']
        ELASTIC_API_USERNAME = os.environ['ELASTIC_API_USERNAME']
        ELASTIC_API_PASSWORD = os.environ['ELASTIC_API_PASSWORD']
        print(ELASTIC_API_URL_HOST)

        self.es = Elasticsearch(host=ELASTIC_API_URL_HOST,
                                scheme='https',
                                port=ELASTIC_API_URL_PORT,
                                http_auth=(ELASTIC_API_USERNAME, ELASTIC_API_PASSWORD))


    def process_item(self, item, spider):
        self.es.index(index='imdb',
                      doc_type='movies',
                      id=uuid.uuid4(),
                      body=item)
        return item
