import os

from dotenv import load_dotenv
from tavily import TavilyClient

especializaciones = {
    "cybersecurity": 3,
    "cyber security": 3,
    "information security": 3,
    "network security": 3,
    "security analyst": 3,
    "security intern": 3,
    "soc": 2,
    "vulnerability": 2,
    "application security": 3
}

ubicaciones = {
    "barcelona": 3,
    "mataró": 5,
    "mataro": 5,
    "badalona": 4,
    "vilassar":3,
    "cabrera":3,
    "premia":3,
    "masnou":3,
    "montgat":3,
    "sant adrià":2,
    "sant andreu":2,
    "llavaneres":3,
    "caldes":3,
    "arenys":2,
}


tipos_trabajo = {
    "intern": 3,
    "internship": 3,
    "trainee": 2,
    "prácticas": 3,
    "practicas": 3,
    "becario": 3,
    "student": 2
}

def puntuacion_localidad(texto):
    puntos = 0
    for ciudad, puntuacion in ubicaciones.items():
        if ciudad in texto:
            print("Ciudad encontrada:", ciudad, "+", puntuacion)
            puntos = max(puntos, puntuacion)
            
    return puntos

def puntuacion_especializacion(texto):
    puntos = 0
    for especializacion, puntuacion in especializaciones.items():
        if especializacion in texto:
            print("Especialización encontrada:", especializacion, "+", puntuacion)
            puntos += puntuacion
            
    return puntos

def puntuacion_tipo_trabajo(texto):
    puntos = 0
    for tipo, puntuacion in tipos_trabajo.items():
        if tipo in texto:
            print("Trabajo encontrado:", tipo, "+", puntuacion)
            puntos = max(puntos,puntuacion)
            
    return puntos

def calculo_puntuacion(texto):
    texto = texto.lower()
    return puntuacion_localidad(texto) + puntuacion_especializacion(texto) + puntuacion_tipo_trabajo(texto)
   

load_dotenv()

api_key = os.getenv("TAIVILY_API_KEY")

cliente = TavilyClient(api_key=api_key)

resultado = cliente.search("Cybersecurity intern Barcelona")

lista_ofertas = []

for oferta in resultado["results"]:
    oferta_normalizada ={
        "titulo" : oferta["title"],
        "url" : oferta["url"],
        "descripcion" : oferta["content"],
        "puntuacion" : oferta["score"]
    }
    lista_ofertas.append(oferta_normalizada)

print("Numero de ofertas encontradas:", len(lista_ofertas))

for oferta in lista_ofertas:
    texto_analisis = oferta["titulo"] + " " + oferta["descripcion"]
    
    puntos_localidad = puntuacion_localidad(texto_analisis.lower())
    puntos_especializacion = puntuacion_especializacion(texto_analisis.lower())
    puntos_tipo_trabajo = puntuacion_tipo_trabajo(texto_analisis.lower())

    puntuacion_total = puntos_localidad + puntos_especializacion + puntos_tipo_trabajo

    print("Titulo:", oferta["titulo"])
    print("URL:", oferta["url"])
    print("Puntos localidad:", puntos_localidad)
    print("Puntos especializacion:", puntos_especializacion)
    print("Puntos tipo trabajo:", puntos_tipo_trabajo)
    print("Puntuacion total:", puntuacion_total)
    print()

