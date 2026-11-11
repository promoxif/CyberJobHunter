import copy
import importlib
import io
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import database
from frontend import ORIGIN, create_app


class MemoryRepository:
    """Explicit injected fixture: never connects to a database or reads .env."""
    def __init__(self):
        self.rows = [dict(id=i, titulo=f'Prácticas de ciberseguridad {i}',
                         url='https://example.org/jobs/1', descripcion='Barcelona · SOC y seguridad de redes.',
                         puntuacion_relevancia=i, prioridad='alta', estado='nueva',
                         fecha_detectada=datetime(2026, 11, 11, 10, 0)) for i in range(1, 29)]

    def listar_ofertas(self, estado=None, prioridad=None, q='', orden='prioridad', pagina=1):
        rows = [r for r in self.rows if (not estado or r['estado'] == estado)
                and (not prioridad or r['prioridad'] == prioridad)
                and (not q or q.lower() in (r['titulo'] + (r['descripcion'] or '')).lower())]
        rows.sort(key=lambda r: r['id'], reverse=True)
        return {'ofertas': copy.deepcopy(rows[(pagina - 1) * 25:pagina * 25]),
                'total': len(rows), 'pagina': pagina, 'tamano': 25}

    def detalle_oferta(self, id_oferta):
        return copy.deepcopy(next((r for r in self.rows if r['id'] == id_oferta), None))

    def actualizar_estado_oferta(self, id_oferta, nuevo_estado):
        for row in self.rows:
            if row['id'] == id_oferta:
                row['estado'] = nuevo_estado
                return 1
        return 0

    def estadisticas_ofertas(self):
        return {estado: sum(r['estado'] == estado for r in self.rows) for estado in database.ESTADOS}


class FrontendTests(unittest.TestCase):
    def setUp(self):
        self.no_connect = patch('database.psycopg.connect', side_effect=AssertionError('Real DB forbidden'))
        self.no_env = patch('database.load_dotenv', side_effect=AssertionError('.env forbidden'))
        self.no_connect.start()
        self.no_env.start()
        self.addCleanup(self.no_connect.stop)
        self.addCleanup(self.no_env.stop)
        self.repo = MemoryRepository()
        self.app = create_app(self.repo)
        self.client = self.app.test_client()
        self.client.get('/', base_url=ORIGIN)
        with self.client.session_transaction(base_url=ORIGIN) as session:
            self.token = session['csrf']

    def get(self, path, **kwargs):
        return self.client.get(path, base_url=ORIGIN, **kwargs)

    def change(self, payload=None, id_oferta=1, **kwargs):
        headers = kwargs.pop('headers', {'Origin': ORIGIN, 'X-CSRF-Token': self.token})
        return self.client.patch(f'/api/ofertas/{id_oferta}/estado', base_url=ORIGIN,
                                 json=payload if payload is not None else {'estado': 'revisada'},
                                 headers=headers, **kwargs)

    def test_page_and_headers(self):
        response = self.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Ofertas nuevas', response.text)
        self.assertIn("frame-ancestors 'none'", response.headers['Content-Security-Policy'])
        self.assertNotIn('unsafe-inline', response.headers['Content-Security-Policy'])
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertEqual(response.headers['Referrer-Policy'], 'no-referrer')
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
        self.assertNotIn('Access-Control-Allow-Origin', response.headers)

    def test_filters_pagination_and_optional_data(self):
        self.assertEqual(len(self.get('/api/ofertas').json['ofertas']), 25)
        self.assertEqual(len(self.get('/api/ofertas?pagina=2').json['ofertas']), 3)
        self.assertEqual(self.get('/api/ofertas?estado=descartada').json['total'], 0)
        self.assertEqual(self.get('/api/ofertas?prioridad=baja').json['total'], 0)
        self.assertEqual(self.get('/api/ofertas?q=inexistente').json['total'], 0)
        self.assertEqual(self.get('/api/ofertas?q=Barcelona&estado=nueva&prioridad=alta').json['total'], 28)
        self.repo.rows[0].update(descripcion=None, puntuacion_relevancia=None, fecha_detectada=None)
        self.assertIsNone(self.get('/api/ofertas/1').json['descripcion'])
        self.repo.rows.clear()
        self.assertEqual(self.get('/api/estadisticas').json['total'], 0)

    def test_reversible_status_persists_and_updates_counts(self):
        for estado in database.ESTADOS:
            self.assertEqual(self.change({'estado': estado}).status_code, 200)
            self.assertEqual(self.get('/api/ofertas/1').json['estado'], estado)
        self.assertEqual(self.get('/api/estadisticas').json['estados']['solicitada'], 1)
        self.assertEqual(self.change(id_oferta=999).status_code, 404)
        self.assertEqual(self.get('/api/ofertas/999').status_code, 404)

    def test_invalid_fields_and_filters(self):
        for payload in ({'estado': 'admin'}, {'estado': 'nueva', 'titulo': 'bad'}, [], {'estado': []}):
            self.assertEqual(self.change(payload).status_code, 400)
        for query in ('orden=DROP+TABLE', 'estado=admin', 'prioridad=urgente', 'pagina=0',
                      'pagina=-1', 'pagina=100001', 'pagina=abc', 'pagina=1&pagina=2',
                      'unknown=1', 'q=' + 'x' * 201):
            self.assertEqual(self.get('/api/ofertas?' + query).status_code, 400, query)
        self.assertEqual(self.get('/api/ofertas/0').status_code, 400)

    def test_csrf_origin_and_host(self):
        for headers in ({}, {'Origin': ORIGIN}, {'X-CSRF-Token': self.token},
                        {'Origin': 'https://evil.example', 'X-CSRF-Token': self.token},
                        {'Origin': ORIGIN, 'X-CSRF-Token': 'wrong'},
                        {'Origin': ORIGIN, 'X-CSRF-Token': 'ñ'}):
            self.assertEqual(self.change(headers=headers).status_code, 403)
        for host in ('localhost:5000', 'evil.example:5000', '127.0.0.1:5001'):
            self.assertEqual(self.get('/', headers={'Host': host}).status_code, 400)
        self.assertEqual(self.get('/', headers={'Sec-Fetch-Site': 'cross-site'}).status_code, 403)
        self.assertEqual(self.get('/api/ofertas/1/estado').status_code, 405)

    def test_secrets_files_and_exception_not_exposed(self):
        for path in ('/.env', '/.env.backup', '/.git/config', '/database.py', '/README.md', '/static/../.env'):
            self.assertEqual(self.get(path).status_code, 404)
        with patch.object(self.repo, 'listar_ofertas', side_effect=RuntimeError('postgres://SECRET_PASSWORD')):
            response = self.get('/api/ofertas')
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('SECRET_PASSWORD', response.text)
        with patch.object(self.repo, 'actualizar_estado_oferta', side_effect=RuntimeError('SECRET')):
            self.assertEqual(self.change().status_code, 503)
            self.assertEqual(self.repo.rows[0]['estado'], 'nueva')

    def test_untrusted_content_and_links(self):
        self.repo.rows[0]['titulo'] = '<script>alert(1)</script>'
        for url in ('javascript:alert(1)', 'data:text/html,test', 'file:///etc/passwd',
                    'https://user:pass@example.org', 'https://example.org\\@evil.org',
                    'https://example.org:invalid', 'http://[broken'):
            self.repo.rows[0]['url'] = url
            data = self.get('/api/ofertas/1').json
            self.assertIsNone(data['url'])
            self.assertEqual(data['titulo'], '<script>alert(1)</script>')
        self.assertNotIn('<script>alert', self.get('/').text)

    def test_body_limit(self):
        response = self.change({'estado': 'nueva', 'extra': 'a' * 5000})
        self.assertEqual(response.status_code, 413)

    def test_imports_do_not_load_env_or_initialize_tavily(self):
        with patch('tavily.TavilyClient', side_effect=AssertionError('Tavily forbidden')):
            import main
            importlib.reload(main)
            with patch('database.consultar_ofertas_cli', return_value=[]) as query:
                # main retains a shared function reference; test through that name.
                with patch.object(main, 'consultar_ofertas_cli', query):
                    self.assertEqual(main.consultar_ofertas_en_db(), [])
                    query.assert_called_once_with('nueva')
            self.assertGreater(main.calculo_puntuacion('cybersecurity intern Barcelona'), 0)

    def test_search_keeps_scoring_and_deduplication(self):
        import main
        with patch.object(main, 'TavilyClient') as client, patch.object(main, 'guardar_ofertas_en_db', return_value=1) as save, patch('sys.stdout', new_callable=io.StringIO):
            client.return_value.search.return_value = {'results': [
                {'url': 'https://example.org/job', 'title': 'Cybersecurity intern Barcelona',
                 'content': 'University student internship', 'score': 0.8}]}
            main.buscar_ofertas()
            self.assertEqual(client.return_value.search.call_count, len(main.busquedas))
            rows = save.call_args.args[0]
            self.assertEqual(len(rows), 1)
            self.assertGreater(rows[0]['puntuacion_relevancia'], 0)
            self.assertIn(rows[0]['prioridad'], database.PRIORIDADES)


class DatabaseQueryTests(unittest.TestCase):
    def test_parameterized_filters_order_and_pagination(self):
        connection = MagicMock()
        cursor = connection.__enter__.return_value.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = {'total': 0}
        cursor.fetchall.return_value = []
        malicious = "'; DROP TABLE ofertas; --%_"
        with patch('database.conectar_db', return_value=connection):
            result = database.listar_ofertas(estado='nueva', prioridad='alta', q=malicious, pagina=2)
        sql, params = cursor.execute.call_args.args
        self.assertNotIn(malicious, sql)
        self.assertIn('CASE prioridad', sql)
        self.assertIn('NULLS LAST', sql)
        self.assertEqual(params[-2:], [25, 25])
        self.assertEqual(params[:2], ['nueva', 'alta'])
        self.assertIn('\\%\\_', params[2])
        self.assertEqual(result['total'], 0)

    def test_update_only_estado(self):
        connection = MagicMock()
        cursor = connection.__enter__.return_value.cursor.return_value.__enter__.return_value
        cursor.rowcount = 1
        with patch('database.conectar_db', return_value=connection):
            self.assertEqual(database.actualizar_estado_oferta(12, 'solicitada'), 1)
            self.assertEqual(database.actualizar_estado_oferta(12, 'invalid'), 0)
        cursor.execute.assert_called_once_with('UPDATE ofertas SET estado = %s WHERE id = %s', ('solicitada', 12))

    def test_connection_encryption_and_timeouts(self):
        with patch.dict('os.environ', {'DATABASE_URL': 'postgresql://fake.invalid/test'}), patch('database.psycopg.connect') as connect:
            database.conectar_db()
            connect.assert_called_once_with('postgresql://fake.invalid/test', sslmode='require', connect_timeout=10)
            connect.return_value.cursor.return_value.__enter__.return_value.execute.assert_called_once_with("SET statement_timeout = '10s'")


if __name__ == '__main__':
    unittest.main()
