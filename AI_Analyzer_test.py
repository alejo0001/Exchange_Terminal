import json
import google.generativeai as genai
from google_news_api import google_news_api
from google_news_api.reponse_classes import EverythingResponse,Article
from typing import List
from common import AnalyzeResponse
from config import generativeAiApiKey
# Configura tu clave de API
genai.configure(api_key=generativeAiApiKey)

model = genai.GenerativeModel('gemini-pro')

googleNewsResponse : EverythingResponse
articles : List[Article]
configPrompt = "I am going to give you the text of a cryptocurrency news item, I want you to analyze the sentiment of said news item. I want you to give me a response in the form of a json object (without including '```json' at the beginning or '```' at the end) where this object takes three elements. The first will be 'text', where your response/analysis will go without it being too extensive. The second element will be 'value' where it will be a number from -10 to 10, where -10 is very bearish, and 10 is very bullish. The third element will be 'coins' where it will be a string array,where will the possible USDT pairs related to the news go, if there are no related pairs, the array will go empty. Please only respond with the json object and the element 'text' in english. This is the text:"

def Analyze():

    AnalysisList : List[AnalyzeResponse] = []
    googleNewsResponse = google_news_api.getArticles()


    articles = googleNewsResponse.articles
    newsItemPrompt = ''

    if(len(articles) > 0):
        for article in articles:
            newsItemPrompt = article.title+'. '+article.description
            response = model.generate_content(configPrompt+newsItemPrompt)
            if(response.text):
                print(response.text)
                datos = json.loads(response.text)
                # print("Texto generado:")
                # print(str(datos))
                # print("análisis: "+datos["text"])
                # print("puntuación: "+str(datos["value"]))

                AnalysisList.append(AnalyzeResponse(
                                    'google',
                                    article.author,
                                    article.url,
                                    article.published_at,
                                    datos['text'],
                                    datos['value'],
                                    datos['coins']

                    )
                )
    else:
        print("Sin resultados: "+str(googleNewsResponse))

    return AnalysisList




