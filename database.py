
import os
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

ESTADOS = ('nueva', 'revisada', 'descartada', 'solicitada')
PRIORIDADES = ('alta', 'media', 'baja')
ORDENES = {
    'prioridad': "CASE prioridad WHEN 'alta' THEN 3 WHEN 'media' THEN 2 WHEN 'baja' THEN 1 ELSE 0 END DESC, puntuacion_relevancia DESC NULLS LAST, fecha_detectada DESC NULLS LAST, id DESC",
    'relevancia': 'puntuacion_relevancia DESC NULLS LAST, fecha_detectada DESC NULLS LAST, id DESC',
    'recientes': 'fecha_detectada DESC NULLS LAST, id DESC',
}
PAGINA_TAMANO = 25


def cargar_configuracion():
    """Only entry points load local configuration; importing modules never does."""
    load_dotenv(Path(__file__).resolve().parent / '.env')

def conectar_db():
    url = os.getenv("DATABASE_URL")

    if not url:
        raise ValueError("DATABASE_URL no configurada")

    conexion = psycopg.connect(url, sslmode="require", connect_timeout=10)
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SET statement_timeout = '10s'")
        conexion.commit()
    except Exception:
        conexion.close()
        raise
    return conexion


def actualizar_estado_oferta(id_oferta, nuevo_estado):
    if nuevo_estado not in ESTADOS:
        return 0
    with conectar_db() as conexion, conexion.cursor() as cursor:
        cursor.execute('UPDATE ofertas SET estado = %s WHERE id = %s',
                       (nuevo_estado, id_oferta))
        return cursor.rowcount


def consultar_ofertas_cli(estado):
    orden = ORDENES['prioridad' if estado == 'nueva' else 'relevancia']
    with conectar_db() as conexion, conexion.cursor() as cursor:
        cursor.execute('SELECT id, titulo, url, puntuacion_relevancia, prioridad '
                       'FROM ofertas WHERE estado = %s ORDER BY ' + orden, (estado,))
        return cursor.fetchall()


def estadisticas_ofertas():
    with conectar_db() as conexion, conexion.cursor() as cursor:
        cursor.execute('SELECT estado, COUNT(*) FROM ofertas GROUP BY estado ORDER BY estado')
        return dict(cursor.fetchall())


def listar_ofertas(estado=None, prioridad=None, q='', orden='prioridad', pagina=1):
    if (estado not in (None, *ESTADOS) or prioridad not in (None, *PRIORIDADES)
            or orden not in ORDENES or not 1 <= pagina <= 100000 or len(q) > 200):
        raise ValueError('Filtros inválidos')
    filtros, valores = [], []
    for columna, valor in (('estado', estado), ('prioridad', prioridad)):
        if valor:
            filtros.append(columna + ' = %s')
            valores.append(valor)
    if q:
        # Treat wildcard characters literally, keeping all user input in parameters.
        patron = '%' + q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
        filtros.append('(titulo ILIKE %s OR descripcion ILIKE %s)')
        valores.extend((patron, patron))
    donde = ' WHERE ' + ' AND '.join(filtros) if filtros else ''
    with conectar_db() as conexion, conexion.cursor(row_factory=dict_row) as cursor:
        cursor.execute('SELECT COUNT(*) AS total FROM ofertas' + donde, valores)
        total = cursor.fetchone()['total']
        cursor.execute(
            'SELECT id, titulo, url, puntuacion_relevancia, prioridad, fecha_detectada, estado '
            'FROM ofertas' + donde + ' ORDER BY ' + ORDENES[orden] + ' LIMIT %s OFFSET %s',
            [*valores, PAGINA_TAMANO, (pagina - 1) * PAGINA_TAMANO])
        return {'ofertas': cursor.fetchall(), 'total': total, 'pagina': pagina,
                'tamano': PAGINA_TAMANO}


def detalle_oferta(id_oferta):
    with conectar_db() as conexion, conexion.cursor(row_factory=dict_row) as cursor:
        cursor.execute('SELECT id, titulo, url, descripcion, puntuacion_relevancia, '
                       'prioridad, fecha_detectada, estado FROM ofertas WHERE id = %s', (id_oferta,))
        return cursor.fetchone()
