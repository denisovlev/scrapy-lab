# -*- coding: utf-8 -*-
import scrapy
import unidecode
import re
import string

#cleanString = lambda x: '' if x is None else unidecode.unidecode(re.sub(r'\s+',' ',x))
def cleanString(x):
    if x is None:
        return ''
    else:
        return unidecode.unidecode(re.sub(r'\s+',' ',x))



class ImdbSpider(scrapy.Spider):

    def __init__(self, name=None, **kwargs):
        super().__init__()
        self.links_movies = []

    name = 'imdb'
    allowed_domains = ['www.imdb.com']
    start_urls = ['https://www.imdb.com/title/tt0096463/fullcredits/']

    def parse(self, response):
        movie_id = cleanString(response.css('meta[property="pageId"]::attr(content)').extract_first())
        movie_name = cleanString(response.css('h3[itemprop="name"] > a[itemprop="url"]::text').extract_first())
        noisy_year = cleanString(response.css('h3[itemprop="name"] > span.nobr::text').extract_first())
        movie_year = int(re.search('(\d+)',noisy_year).group(1))
        rows = response.css('table.cast_list tr')
        for r in rows:
            actor_url = cleanString(r.css('td[itemprop="actor"] a[itemprop="url"]::attr(href)').extract_first())
            if not actor_url: continue

            actor_name = cleanString(r.css('td[itemprop="actor"] span::text').extract_first())
            actor_id = re.search('/name/(.+?)/',actor_url).group(1)
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

    def parse_actor_movies(self, response):
        rows = response.css('div#filmo-head-actor+div.filmo-category-section>div')
        for r in rows:
            moviedate = int(r.css('span.year_column::text'))
            if moviedate > 1989 or moviedate < 1980: continue
            movie_id = r.css('::attr(id)').extract_first()
            movie_link = re.search('actor-(.+?)',movie_id).group(1)
            self.start_urls.append('https://www.imdb.com/title/'+movie_link+'/fullcredits/')

    def parse_actor_bio(self, response):
        item = response.meta['item']
        if not response.css('#overviewTable').extract_first(): return item
        birthdate = cleanString(response.css('#overviewTable tr:nth_child(1) time::attr(datetime)').extract_first())
        birthname = ''
        birthname_label = cleanString(response.css('#overviewTable tr:nth_child(2) td:nth_child(1)::text').extract_first())
        if birthname_label == 'Birth Name':
            birthname = cleanString(response.css('#overviewTable tr:nth_child(2) td:nth_child(2)::text').extract_first())
        height = cleanString(response.css('#overviewTable tr:nth_child(3) td:nth_child(2)::text').extract_first())
        item.update({
            'birthdate': birthdate,
            'birthname': birthname,
            'height': height
        })
        return item





#characters = [i.strip() for i in noisy_character]

# or

#character = list(map(lambda s: s.strip(), noisy_character))