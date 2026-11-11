"""Visual QA only: python tests/preview_fixture.py (no .env or Supabase)."""
import logging
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from frontend import create_app
from test_frontend import MemoryRepository

repo = MemoryRepository()
titles = ['Cybersecurity Intern — Security Operations', 'Prácticas de analista de ciberseguridad',
          'Information Security Trainee', 'Junior Application Security Analyst',
          'Prácticas en seguridad de redes', 'SOC Analyst Intern']
for index, row in enumerate(repo.rows):
    row['titulo'] = titles[index % len(titles)]
    row['prioridad'] = ['alta', 'media', 'baja'][index % 3]
    row['estado'] = ['nueva', 'nueva', 'nueva', 'revisada', 'solicitada', 'descartada'][index % 6]
    row['descripcion'] = ('DATOS FICTICIOS PARA REVISIÓN VISUAL.\n\nBuscamos estudiantes de Ingeniería Informática '
                          'con interés en ciberseguridad para colaborar con el equipo de seguridad.\n\n'
                          'Participarás en el análisis de alertas, la investigación de vulnerabilidades y '
                          'la mejora de procedimientos de respuesta.\n\nBarcelona · Prácticas · Formación continua.')
logging.getLogger('werkzeug').disabled = True
create_app(repo).run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
