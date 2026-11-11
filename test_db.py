
from database import conectar_db

with conectar_db() as conexion:
    with conexion.cursor() as cursor:
        cursor.execute("""
            INSERT INTO ofertas (
                titulo,
                url,
                descripcion,
                puntuacion_relevancia,
                prioridad
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (url) DO NOTHING
        """, (
            "Oferta de prueba",
            "https://example.com/test-cyberjobhunter",
            "Prueba de conexion con Supabase",
            20,
            "alta"
        ))

print("Prueba de insercion completada.")
