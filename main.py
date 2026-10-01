import os

from dotenv import load_dotenv
from tavily import TavilyClient

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
    if "barcelona" in oferta["titulo"].lower() or "barcelona" in oferta["descripcion"].lower():
        print("Titulo:", oferta["titulo"])
        print("URL:", oferta["url"])
        print()


