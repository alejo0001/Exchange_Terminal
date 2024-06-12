from newsapi import NewsApiClient
from common import subtratcFromCurrentDate
from google_news_api.reponse_classes import EverythingResponse,Article,Source
from typing import List
from config import googleNewsApiKey
# Init
newsapi = NewsApiClient(api_key=googleNewsApiKey)


# /v2/everything
all_articles: EverythingResponse = newsapi.get_everything(q='Crypto',
                                      #sources='bbc-news,the-verge',
                                      #domains='bbc.co.uk,techcrunch.com',
                                      from_param= subtratcFromCurrentDate('20h').strftime("%Y-%m-%dT%H:%M:%S"),#'2024-06-08T17:19:00',
                                      #to='2017-12-12',
                                      #language='en',
                                      sort_by='popularity',
                                      #page=2
                                      )

def getArticles():
    articles: List[Article] = []
    source : Source
    for article in all_articles['articles']:
        source = Source(article['source']['id'],article['source']['name'])
        articles.append(Article(
                            source,
                            article['author'],
                            article['title'],
                            article['description'],
                            article['url'],
                            article['urlToImage'],
                            article['publishedAt'],
                            article['content']
                                )
                        )
    return EverythingResponse(all_articles['status'],int(all_articles['totalResults']),articles) 

# print('resultado: ')
# print(all_articles)
