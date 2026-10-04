import os
import re

from dotenv import load_dotenv
from tavily import TavilyClient

especializaciones = {
    "cybersecurity": {
        "palabras": ["cybersecurity", "cyber security","ciberseguridad"],
        "puntos": 3
    },

    "information security": {
        "palabras": ["information security", "información de seguridad", "seguridad informática"],
        "puntos": 3
    },

    "network security": {
        "palabras": ["network security", "seguridad de redes", "seguridad de red"],
        "puntos": 3
    },

    "security analyst": {
        "palabras": ["security analyst", "analista de seguridad"],
        "puntos": 3
    },

    "application security": {
        "palabras": ["application security", "seguridad de aplicaciones"],
        "puntos": 3
    },

    "vulnerability": {
        "palabras": ["vulnerability", "vulnerabilidad"],
        "puntos": 2
    },

    "soc": {
        "palabras": ["soc", "centro de operaciones de seguridad"],
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
    "becaria": 3,
    "estudiante": 2,
    "formación": 1,
    "formacion": 1,
    "programa de prácticas": 3,
    "pgrama de practicas": 3,
}

potencial_oferta_positivo = {
    "job": 1,
    "position": 2,
    "role": 2,
    "vacancy": 3,
    "opening": 3,
    "hiring": 3,
    "intern": 1,
    "internship": 2,
    "prácticas": 2,
    "becario": 2,
    "trainee": 1
}

potencial_oferta_negativo = {
    "course": -3,
    "market trends": -5,
    "list of": -4,
    "jobs in": -5,
    "jobs near": -5,
    "search results": -5
}

indicadores_agregador = [
    "jobs in",
    "jobs near",
    "search results",
    "list of",
    "jobs, employment",
]

orden_prioridad = {
    "alta": 3,
    "media": 2,
    "baja": 1
}

busquedas = [
    "prácticas de ciberseguridad Barcelona",
    "prácticas de seguridad informática Barcelona",
    "prácticas de seguridad de redes Barcelona",
    "prácticas analista de seguridad Barcelona",
    "prácticas seguridad de aplicaciones Barcelona",

    "cybersecurity intern Barcelona",
    "information security intern Barcelona",
    "network security intern Barcelona",
    "security analyst intern Barcelona",
    "application security intern Barcelona"
]

busquedas_pruebas = [
    "prácticas de ciberseguridad Barcelona",
    "network security intern Barcelona"
]

def puntuacion_localidad(texto):
    puntos = 0
    for ciudad, puntuacion in ubicaciones.items():
        if re.search(r"(?<!\w)" + re.escape(ciudad) + r"(?!\w)", texto):          
            puntos = max(puntos, puntuacion)
    return puntos

def puntuacion_especializacion(texto):
    puntos = 0

    for especializacion, datos in especializaciones.items():
        for palabra in datos["palabras"]:
            patron = r"(?<!\w)" + re.escape(palabra) + r"(?!\w)"
            if re.search(patron, texto):
                puntos += datos["puntos"]
                break
    return puntos

def puntuacion_tipo_trabajo(texto):
    puntos = 0
    for tipo, puntuacion in tipos_trabajo.items():
        if re.search(r"(?<!\w)" + re.escape(tipo) + r"(?!\w)", texto):
            puntos = max(puntos,puntuacion)
            
    return puntos

def calculo_puntuacion(texto):
    texto = texto.lower()
    return puntuacion_localidad(texto) + puntuacion_especializacion(texto) + puntuacion_tipo_trabajo(texto)

def calcular_prioridad(texto):
    puntos = 0
    positivas_encontradas = []
    negativas_encontradas = []

    for palabra,puntuacion in potencial_oferta_positivo.items():
        if palabra in texto:
            positivas_encontradas.append(palabra)
            puntos += puntuacion

    for palabra,puntuacion in potencial_oferta_negativo.items():
        if palabra in texto:
            negativas_encontradas.append(palabra)
            puntos -= puntuacion

    for indicador in indicadores_agregador:
        if indicador in texto:
            puntos -= 5

    if re.search(r"\d+\s+(jobs|internships|startups)", texto):
        puntos -= 5
    return puntos

def obtener_prioridad(texto):
    texto = texto.lower()
    puntuacion_oferta = calcular_prioridad(texto)

    if puntuacion_oferta >= 8:
        return "alta"
    elif puntuacion_oferta >= 3:
        return "media"
    else:
        return "baja"

load_dotenv()

api_key = os.getenv("TAIVILY_API_KEY")

cliente = TavilyClient(api_key=api_key)

lista_ofertas = []
urls_obtenidas = set()

for busqueda in busquedas:
    resultado = cliente.search(busquedas_pruebas,max_results=20)
    for oferta in resultado["results"]:
        if oferta["url"] in urls_obtenidas:
            continue

        urls_obtenidas.add(oferta["url"])
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
    prioridad_oferta = obtener_prioridad(texto_analisis)
    puntuacion_total = calculo_puntuacion(texto_analisis)

    oferta["puntuacion_relevancia"] = puntuacion_total
    oferta["prioridad"] = prioridad_oferta

    

lista_ofertas.sort(
    key=lambda oferta: (
        -oferta["puntuacion_relevancia"],
        -orden_prioridad[oferta["prioridad"]],
        oferta["titulo"].lower()
    )
)

print("====================================")
for oferta in lista_ofertas:
    print(oferta["titulo"])
    print()
    print("Puntuacion:", oferta["puntuacion_relevancia"])
    print("Prioridad:", oferta["prioridad"])
    print("URL:", oferta["url"])
    print("====================================")
    print()
