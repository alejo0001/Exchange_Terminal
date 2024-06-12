from time import sleep
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from AI_Analyzer_test import Analyze
from common import AnalyzeResponse,SendTelegramMessage
from typing import List
import asyncio
app = FastAPI()
AnalysisList:List[AnalyzeResponse]=[]

#ejemplo validación de datos con baseModel:
class Libro(BaseModel):
    titulo:str
    autor:str
    paginas:int
    editorial:Optional[str]

#http://127.0.0.1:8000/
@app.get("/")
def index():
    return {"message":"Prueba FastAPI"}

@app.get("/{id}")
def pruebaId(id:int):
    return {"id":id}

@app.post("/libros")
def insertar_libro(libro:Libro):
    return{"message": f"libro {libro.titulo} insertado"}

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(AIAnalysis()) 

print ('server en funcionamiento')
async def AIAnalysis():
    counter : int = 0
    
    while True:
        if(counter == 0):
            counter = 1
            AnalysisList = Analyze()
            messages : str =''
            for item in AnalysisList:
                if(item.score is not None and abs(int(item.score)) >= 1):
                    messages+=f'''noticia: {item.newsItemLink}
análisis: {item.analysis}
puntaje: {item.score}
fecha: {item.newsItemDate}
pares: {str(item.pairs)}
'''
                # print('análisis: '+str(item.analysis))
            print(messages)
            if(messages):
                await SendTelegramMessage(messages)
            
        await asyncio.sleep(540)
        counter = 0


# if __name__ == "__main__":
#     asyncio.run(AIAnalysis())

#print('análisis: '+str(item.analysis))

#da60d6cb5ee743b3aa090e1121ad2247 API KEY GOOGLE NEWS


