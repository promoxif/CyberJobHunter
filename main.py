import os

from dotenv import load_dotenv
from tavily import TavilyClient

palabras_ciberseguridad = [
    "cybersecurity",
    "cyber security",
    "information security",
    "network security",
    "security analyst",
    "security intern",
    "soc",
    "vulnerability",
    "application security"
]

palabras_ubicacion = [
    "barcelona",
    "mataró",
    "mataro",
    "badalona"
]

palabras_practicas = [
    "intern",
    "internship",
    "trainee",
    "prácticas",
    "practicas",
    "becario",
    "student"
]

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
    texto_analisis = oferta["titulo"].lower() + " " + oferta["descripcion"].lower()
    
    es_ciberseguridad = any(palabra in texto_analisis for palabra in palabras_ciberseguridad)
    es_ubicacion = any(palabra in texto_analisis for palabra in palabras_ubicacion)
    es_practicas = any(palabra in texto_analisis for palabra in palabras_practicas)

    if es_ciberseguridad and es_ubicacion and es_practicas:
        print("Titulo:", oferta["titulo"])
        print("URL:", oferta["url"])
        print()


