"""Private loopback dashboard. Importing this module never loads local secrets."""
import logging
import secrets
import sys
import threading
import webbrowser
from datetime import date, datetime
from urllib.parse import urlsplit

from flask import Flask, abort, jsonify, render_template, request, session
from werkzeug.exceptions import HTTPException

import database

ORIGIN = 'http://127.0.0.1:5000'


def oferta_publica(oferta):
    resultado = dict(oferta)
    try:
        url = urlsplit(resultado.get('url') or '')
        _ = url.port  # Reject malformed ports before passing links to the browser.
        if (url.scheme not in ('http', 'https') or not url.hostname or url.username
                or url.password or any(ord(c) < 33 for c in resultado['url'])
                or '\\' in resultado['url']):
            raise ValueError('Enlace inválido')
        resultado['dominio'] = url.hostname
    except ValueError:
        resultado['url'] = None
        resultado['dominio'] = 'Enlace no disponible'
    for campo, valor in resultado.items():
        if isinstance(valor, (date, datetime)):
            resultado[campo] = valor.isoformat()
    return resultado


def create_app(repository=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=secrets.token_hex(32),
        TRUSTED_HOSTS=['127.0.0.1'],
        MAX_CONTENT_LENGTH=4096,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Strict',
        SESSION_COOKIE_NAME='cyberjobhunter_session',
        DEBUG=False,
    )
    repo = repository if repository is not None else database

    @app.before_request
    def proteger_peticion():
        # Exact host/port validation additionally prevents DNS rebinding.
        if request.host != '127.0.0.1:5000':
            abort(400)
        if request.headers.get('Sec-Fetch-Site') == 'cross-site':
            abort(403)
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            if request.headers.get('Origin') != ORIGIN:
                abort(403)
            token = request.headers.get('X-CSRF-Token', '')
            esperado = session.get('csrf', '')
            if not esperado or not token.isascii() or not secrets.compare_digest(token, esperado):
                abort(403)

    @app.after_request
    def proteger_respuesta(response):
        response.headers.update({
            'Content-Security-Policy': "default-src 'none'; script-src 'self'; style-src 'self'; "
                "connect-src 'self'; img-src 'self'; font-src 'self'; base-uri 'none'; "
                "form-action 'none'; frame-ancestors 'none'; object-src 'none'",
            'X-Frame-Options': 'DENY',
            'X-Content-Type-Options': 'nosniff',
            'Referrer-Policy': 'no-referrer',
            'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
            'Cache-Control': 'no-store',
        })
        return response

    @app.errorhandler(Exception)
    def error_seguro(error):
        codigo = error.code if isinstance(error, HTTPException) else 503
        mensajes = {
            400: 'Petición no válida. Revisa los filtros.',
            403: 'Petición bloqueada. Recarga el panel y vuelve a intentarlo.',
            404: 'No se ha encontrado este recurso.',
            405: 'Operación no permitida.',
            413: 'La petición supera el tamaño permitido.',
            415: 'Se requiere contenido JSON.',
        }
        # Never log exception strings: database drivers may include credentials.
        return jsonify(error=mensajes.get(codigo, 'No se han podido obtener o guardar los datos. Inténtalo de nuevo.')), codigo

    @app.get('/')
    def inicio():
        if 'csrf' not in session:
            session['csrf'] = secrets.token_urlsafe(32)
        return render_template('index.html', csrf=session['csrf'])

    @app.get('/api/ofertas')
    def ofertas():
        permitidos = {'estado', 'prioridad', 'q', 'orden', 'pagina'}
        if set(request.args) - permitidos or any(len(request.args.getlist(k)) != 1 for k in request.args):
            abort(400)
        estado = request.args.get('estado') or None
        prioridad = request.args.get('prioridad') or None
        q = request.args.get('q', '').strip()
        orden = request.args.get('orden', 'prioridad')
        pagina_texto = request.args.get('pagina', '1')
        if (estado not in (None, *database.ESTADOS)
                or prioridad not in (None, *database.PRIORIDADES)
                or orden not in database.ORDENES or len(q) > 200
                or not pagina_texto.isascii() or not pagina_texto.isdigit()
                or len(pagina_texto) > 6 or not 1 <= int(pagina_texto) <= 100000):
            abort(400)
        resultado = repo.listar_ofertas(estado=estado, prioridad=prioridad,
                                       q=q, orden=orden, pagina=int(pagina_texto))
        resultado['ofertas'] = [oferta_publica(o) for o in resultado['ofertas']]
        return jsonify(resultado)

    @app.get('/api/ofertas/<int:id_oferta>')
    def detalle(id_oferta):
        if not 1 <= id_oferta <= 2147483647:
            abort(400)
        oferta = repo.detalle_oferta(id_oferta)
        if oferta is None:
            abort(404)
        return jsonify(oferta_publica(oferta))

    @app.get('/api/estadisticas')
    def estadisticas():
        datos = repo.estadisticas_ofertas()
        return jsonify(estados={estado: datos.get(estado, 0) for estado in database.ESTADOS},
                       total=sum(datos.values()))

    @app.patch('/api/ofertas/<int:id_oferta>/estado')
    def actualizar(id_oferta):
        datos = request.get_json()
        if (not 1 <= id_oferta <= 2147483647 or not isinstance(datos, dict)
                or set(datos) != {'estado'} or datos['estado'] not in database.ESTADOS):
            abort(400)
        if not repo.actualizar_estado_oferta(id_oferta, datos['estado']):
            abort(404)
        return jsonify(id=id_oferta, estado=datos['estado'])

    return app


if __name__ == '__main__':
    database.cargar_configuracion()
    # Access logs would otherwise retain search terms in query strings.
    logging.getLogger('werkzeug').disabled = True
    print(f'CyberJobHunter · Abre {ORIGIN} · Ctrl+C para salir')
    if '--open-browser' in sys.argv:
        opener = threading.Timer(1.5, webbrowser.open, args=(ORIGIN,))
        opener.daemon = True
        opener.start()
    create_app().run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
