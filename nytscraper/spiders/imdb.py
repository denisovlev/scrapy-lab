# -*- coding: utf-8 -*-
import datetime

import scrapy
import unidecode
import re

def cleanString(x):
    if x is None:
        return ''
    else:
        return unidecode.unidecode(re.sub(r'\s+',' ',x))

class ImdbSpider(scrapy.Spider):

    name = 'imdb'
    allowed_domains = ['www.imdb.com']
    start_urls = ['https://www.imdb.com/title/tt0096463/fullcredits/']
    movie_actor = {}

    def parse(self, response):
        movie_id = cleanString(response.css('meta[property="pageId"]::attr(content)').extract_first())
        movie_name = cleanString(response.css('h3[itemprop="name"] > a[itemprop="url"]::text').extract_first())
        print(movie_name)
        noisy_year = cleanString(response.css('h3[itemprop="name"] > span.nobr::text').extract_first())
        movie_year = int(re.search('(\d+)',noisy_year).group(1))
        rows = response.css('table.cast_list tr')
        for r in rows:
            actor_url = cleanString(r.css('td[itemprop="actor"] a[itemprop="url"]::attr(href)').extract_first())
            if not actor_url: continue

            actor_name = cleanString(r.css('td[itemprop="actor"] span::text').extract_first())
            actor_id = re.search('/name/(.+?)/',actor_url).group(1)
            if self.check_movie_actor_pair(movie_id, actor_id): continue
            self.add_movie_actor_pair(movie_id, actor_id)
            noisy_role = ''.join(r.css('td.character ::text').extract())
            noisy_character = cleanString(noisy_role)
            role_name = noisy_character.strip()
            json = {
                'movie_id': movie_id,
                'movie_name': movie_name,
                'movie_year': movie_year,
                'actor_name': actor_name,
                'actor_id': actor_id,
                'role_name': role_name,
            }
            request = response.follow('https://www.imdb.com/name/'+actor_id+'/bio', callback=self.parse_actor_bio)
            request.meta['item'] = json
            yield request
            request2 = response.follow('https://www.imdb.com/name/' + actor_id, callback=self.parse_actor_movies)
            request2.meta['actor'] = actor_id
            yield request2

    def parse_actor_movies(self, response):
        actor_id = response.meta['actor']
        rows = response.css('#filmo-head-actor+div.filmo-category-section>div, #filmo-head-actress+div.filmo-category-section>div')
        for r in rows:
            if 'TV Series' in ''.join(r.css('::text').extract()): continue
            year_string = r.css('span.year_column::text').extract_first().strip()
            if not year_string: continue
            moviedate = int(year_string[:4])
            if moviedate > 1989 or moviedate < 1980: continue
            movie_id = re.search('(?:actor|actress)-(.+)', r.css('::attr(id)').extract_first()).group(1)
            movie_url = 'https://www.imdb.com/title/' + movie_id + '/fullcredits/'
            if self.check_movie_actor_pair(movie_id, actor_id) :continue
            yield response.follow(movie_url, callback=self.parse)

    def parse_actor_bio(self, response):
        item = response.meta['item']
        if not response.css('#overviewTable').extract_first(): return item
        tr = response.css('#overviewTable tr')
        birthdate = ''
        birthname = ''
        height = ''
        for r in tr:
            label = r.css('td.label::text').extract_first()
            if label == 'Born':
                string_birthdate = cleanString(r.css('time::attr(datetime)').extract_first())
                # parse date string
                birthdate = datetime.datetime.strptime(string_birthdate, '%Y-%m-%d').strftime('%Y-%m-%d')
                continue
            if label == 'Birth Name': birthname = cleanString(r.css('td:nth_child(2)::text').extract_first()); continue
            if label == 'Height': height = self.get_height(r); continue
        item.update({
            'birthdate': birthdate,
            'birthname': birthname,
            'height': height
        })
        return item

    def get_height(self, r):
        noisy_height = cleanString(r.css('td:nth_child(2)::text').extract_first())
        height = float(re.search('(\d+\.\d+)\sm', noisy_height).group(1))
        return height

    def create_movie_actor_key(self, m_id, a_id):
        return m_id + '_' + a_id

    def add_movie_actor_pair(self, movie_id, actor_id):
        self.movie_actor[self.create_movie_actor_key(movie_id,actor_id)] = 1

    def check_movie_actor_pair(self, movie_id, actor_id):
        if self.create_movie_actor_key(movie_id, actor_id) in self.movie_actor: print('PAIR REPEATED: ' + movie_id + ' ' + actor_id); return True
        return False
