import os
import re

from dotenv import load_dotenv
from tavily import TavilyClient

especializaciones = {
    "cybersecurity": {
        "palabras": ["cybersecurity", "cyber security"],
        "puntos": 3
    },

    "information security": {
        "palabras": ["information security"],
        "puntos": 3
    },

    "network security": {
        "palabras": ["network security"],
        "puntos": 3
    },

    "security analyst": {
        "palabras": ["security analyst"],
        "puntos": 3
    },

    "application security": {
        "palabras": ["application security"],
        "puntos": 3
    },

    "vulnerability": {
        "palabras": ["vulnerability"],
        "puntos": 2
    },

    "soc": {
        "palabras": ["soc"],
        "puntos": 2
    }
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
    "traineeship": 2,
    "prácticas": 3,
    "practicas": 3,
    "becario": 3,
    "student": 2
}

def puntuacion_localidad(texto):
    puntos = 0
    for ciudad, puntuacion in ubicaciones.items():
        if re.search(r"(?<!\w)" + re.escape(ciudad) + r"(?!\w)", texto):
            print("Ciudad encontrada:", ciudad, "+", puntuacion)            
            puntos = max(puntos, puntuacion)
            
    print("Puntos localidad:", puntos)
    return puntos

def puntuacion_especializacion(texto):
    puntos = 0

    for especializacion, datos in especializaciones.items():

        for palabra in datos["palabras"]:

            patron = r"(?<!\w)" + re.escape(palabra) + r"(?!\w)"

            if re.search(patron, texto):
                print("Especialización encontrada:", especializacion, "+", datos["puntos"])
                puntos += datos["puntos"]
                break

    print("Puntos especialización:", puntos)
    return puntos

def puntuacion_tipo_trabajo(texto):
    puntos = 0
    for tipo, puntuacion in tipos_trabajo.items():
        if re.search(r"(?<!\w)" + re.escape(tipo) + r"(?!\w)", texto):
            print("Trabajo encontrado:", tipo, "+", puntuacion)
            puntos = max(puntos,puntuacion)
            
    print("Puntos tipo trabajo:", puntos)
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

    puntuacion_total = calculo_puntuacion(texto_analisis)

    print("Titulo:", oferta["titulo"])
    print("URL:", oferta["url"])
    print("Puntuacion total:", puntuacion_total)
    print()
