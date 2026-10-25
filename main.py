import os
import re
import sqlite3

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
    "barcelona": 20,
    "mataró": 25,
    "mataro": 25,
    "badalona": 22,
    "vilassar": 15,
    "cabrera": 15,
    "premia": 15,
    "premià": 15,
    "masnou": 15,
    "montgat": 15,
    "sant adrià": 10,
    "sant adria": 10,
    "sant andreu": 10,
    "llavaneres": 12,
    "caldes": 12,
    "arenys": 10,
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
    "programa de practicas": 3,
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

penalizaciones_oferta = {
    "market trends": -5,
    "list of": -4,
    "search results": -5,
    "senior": -5,
    "manager": -5,
    "director": -5,
    "bootcamp": -5,
    "master": -3,
    "article": -5,
    "artículo": -5,
    "news": -5,
    "noticias": -5
}

orden_prioridad = {
    "alta": 3,
    "media": 2,
    "baja": 1
}

perfil_academico = [ 
    "student",
    "university student",
    "undergraduate",
    "final year",
    "last year",
    "estudiante",
    "universitario",
    "último curso",
    "4º curso"
]

fechas = [
    "january 2027",
    "enero 2027",
    "january, 2027",
    "enero, 2027"
]
    


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
def mostrar_menu():
    print("====================================")
    print("Bienvenido al sistema de gestión de ofertas de trabajo")
    print("1. Buscar nuevas ofertas")
    print("2. Consultar ofertas nuevas")
    print("3. Consultar candidaturas enviadas")
    print("4. Ver estadísticas de ofertas")
    print("5. Salir")
    print("====================================")
    
    opcion = input("Ingresa el numero de la opcion: ")
    return opcion

def buscar_ofertas():
    lista_ofertas = []
    urls_obtenidas = set()
    for busqueda in busquedas_pruebas:
        resultado = cliente.search(busqueda,max_results=20)
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

    nuevas_ofertas = guardar_ofertas_en_db(lista_ofertas)
    print("Numero de nuevas ofertas guardadas en la base de datos:", nuevas_ofertas)

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

def puntuacion_perfil_academico(texto):
    for tipo in perfil_academico:
        if re.search(r"(?<!\w)" + re.escape(tipo) + r"(?!\w)", texto):
            return 2
            
    return 0

def puntuacion_fechas(texto):
    for tipo in fechas:
        if re.search(r"(?<!\w)" + re.escape(tipo) + r"(?!\w)", texto):
            return 3
            
    return 0

def calculo_puntuacion(texto):
    texto = texto.lower()
    return puntuacion_localidad(texto) + puntuacion_especializacion(texto) + puntuacion_tipo_trabajo(texto) + puntuacion_perfil_academico(texto) + puntuacion_fechas(texto)

def calcular_prioridad(texto):
    puntos = 0

    for palabra,puntuacion in potencial_oferta_positivo.items():
         if re.search(r"(?<!\w)" + re.escape(palabra) + r"(?!\w)", texto):
            puntos += puntuacion

    for palabra,puntuacion in penalizaciones_oferta.items():
        if re.search(r"(?<!\w)" + re.escape(palabra) + r"(?!\w)", texto):
            puntos += puntuacion

    if re.search(r"\d+\s+(jobs|internships|startups|empleos|ofertas)", texto):
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

def iniciar_base_de_datos():
    conexion = sqlite3.connect("ofertas.db")
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ofertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            puntuacion_relevancia INTEGER,
            prioridad TEXT,
            fecha_detectada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            estado TEXT NOT NULL DEFAULT 'nueva',
        )
    """)

    conexion.commit()
    conexion.close()

def guardar_ofertas_en_db(lista_ofertas):
    conexion = sqlite3.connect("ofertas.db")
    cursor = conexion.cursor()

    nuevas = 0

    for oferta in lista_ofertas:
        try:
            cursor.execute("""
                INSERT INTO ofertas (titulo, url, descripcion, puntuacion_relevancia, prioridad, fecha_detectada)
                VALUES (?, ?, ?, ?, ?, datetime('now'))""",
                (
                    oferta["titulo"], oferta["url"], oferta["descripcion"], oferta["puntuacion_relevancia"], oferta["prioridad"]
                ))
            nuevas += 1

        except sqlite3.IntegrityError:
            pass # La oferta ya existe en la base de datos, se ignora
            

    conexion.commit()
    conexion.close()
    return nuevas

def consultar_ofertas_en_db():
    conexion = sqlite3.connect("ofertas.db")
    cursor = conexion.cursor()

    cursor.execute("""
                   SELECT id, titulo, url, puntuacion_relevancia, prioridad FROM ofertas
                   WHERE estado = 'nueva'
                   ORDER BY CASE prioridad 
                   WHEN 'alta' THEN 3 
                   WHEN 'media' THEN 2 
                   WHEN 'baja' THEN 1 
                   ELSE 0 
                   END DESC, 
                   puntuacion_relevancia DESC
                   """)
    
    ofertas = cursor.fetchall()
    conexion.close()
    return ofertas

def actualizar_estado_oferta(id_oferta, nuevo_estado):
    estados_validos = ["nueva", "revisada", "descartada", "solicitada"]
    if nuevo_estado not in estados_validos:
        print("Estado no valido")
        return 0

    conexion = sqlite3.connect("ofertas.db")
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE ofertas
        SET estado = ?
        WHERE id = ?
    """, (nuevo_estado, id_oferta))

    conexion.commit()
    filas_actualizadas = cursor.rowcount
    conexion.close()
    return filas_actualizadas

def catalogar_ofertas(lista_ofertas_db):
    print("====================================") 
    print()

    for(id_oferta,titulo, url, puntuacion_relevancia, prioridad) in lista_ofertas_db:
        print("ID:", id_oferta, "  ", titulo)
        print("Puntuacion:", puntuacion_relevancia)
        print("Prioridad:", prioridad.upper())
        print("URL:", url)
        print()
        print("Que quieres hacer con esta oferta?")
        print("1. Marcar como revisada")
        print("2. Marcar como descartada")
        print("3. Marcar como solicitada")

        seguir= False
        while(seguir == False): 
            opcion = input("Ingresa el numero de la opcion: ")

            match opcion:
                case "1":
                    nuevo_estado = "revisada"
                    seguir = True
                case "2":
                    nuevo_estado = "descartada"
                    seguir = True
                case "3":
                    nuevo_estado = "solicitada"
                    seguir = True
                case _:
                    print("Opcion incorrecta !!!!!!!!!!!!!!!!")
                    print()

        mensaje_actualizacion=actualizar_estado_oferta(id_oferta, nuevo_estado)
        print("Se han actualizado", mensaje_actualizacion, "la oferta con id:", id_oferta, "ha cambiado al estado:", nuevo_estado)
        print()
        print("====================================")
        print()
        
def consultar_ofertas_en_db_solicitades():
    conexion = sqlite3.connect("ofertas.db")
    cursor = conexion.cursor()
    
    cursor.execute("""
                       SELECT id, titulo, url, puntuacion_relevancia, prioridad FROM ofertas
                       WHERE estado = 'solicitada'
                       ORDER BY CASE prioridad 
                       WHEN 'alta' THEN 3 
                       WHEN 'media' THEN 2 
                       WHEN 'baja' THEN 1 
                       ELSE 0 
                       END DESC, 
                       puntuacion_relevancia DESC
                       """)
        
    ofertas = cursor.fetchall()
    conexion.close()
    return ofertas      

def mostrar_ofertas(lista_ofertas_db):
    print("====================================") 
    print()

    for(id_oferta,titulo, url, puntuacion_relevancia, prioridad) in lista_ofertas_db:
        print("ID:", id_oferta, "  ", titulo)
        print("Puntuacion:", puntuacion_relevancia)
        print("Prioridad:", prioridad.upper())
        print("URL:", url)
        print()
        print("====================================")
        print()  
def mostar_estadisticas():
    conexion = sqlite3.connect("ofertas.db")
    cursor = conexion.cursor()
    
    cursor.execute("""
            SELECT estado, COUNT(*) FROM ofertas
            GROUP BY estado
    """)
        
    estadisticas = cursor.fetchall()
    conexion.close()
    
    print("====================================") 
    print()
    print("Estadísticas de ofertas:")
    for estado, cantidad in estadisticas:
        print(f"Estado: {estado}, Cantidad: {cantidad}")
        print()
        print("====================================")

### main -----------------------------------------------------------------------------------------------------------------------------------------------------------

load_dotenv()

api_key = os.getenv("TAVILY_API_KEY")

cliente = TavilyClient(api_key=api_key)

iniciar_base_de_datos()
salir = False

while(salir == False):
    menu_opcion = mostrar_menu()

    if(menu_opcion == "1"):
        buscar_ofertas()
    elif(menu_opcion == "2"):
        lista_ofertas_db = consultar_ofertas_en_db()
        catalogar_ofertas(lista_ofertas_db)
    elif(menu_opcion == "3"):
        lista_ofertas_db = consultar_ofertas_en_db_solicitades()
        mostrar_ofertas(lista_ofertas_db)
    elif(menu_opcion == "4"):
        mostar_estadisticas()
    elif(menu_opcion == "5"):
        salir = True

print("Saliendo del programa...")
exit()  