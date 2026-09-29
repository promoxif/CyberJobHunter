import requests

respuesta = requests.get("https://httpbin.org/get")

print ("Codigo:",respuesta.status_code)

datos = respuesta.json()

print("URL:",datos["url"])
print("IP:",datos["origin"])
print("User-Agent:",datos["headers"]["User-Agent"])
