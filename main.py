import os

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

api_key = os.getenv("TAIVILY_API_KEY")

cliente = TavilyClient(api_key=api_key)

resultado = cliente.search("Cybersecurity intern Barcelona")

print(resultado)