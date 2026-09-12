"""Configuração local da suíte: SQLite em memória e IA sem chamadas externas."""

import os

# Esses valores precisam existir antes de importar settings, que carrega o .env.
# Assim, executar pytest não tenta criar um banco de testes no Supabase configurado
# para a demo. A alteração vale apenas para este processo de testes.
os.environ.update(
    DATABASE_URL="",
    DJANGO_DEBUG="True",
    DJANGO_SECRET_KEY="opsmind-test-only-key",
    AI_PROVIDER="mock",
    GEMINI_API_KEY="",
    GEMINI_MODEL="",
)

from .settings import *  # noqa: E402,F403

# O banco é descartável; fixtures podem executar seed/reset/flush sem tocar na demo.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        # A suíte continua em memória. QA manual pode apontar explicitamente para
        # um SQLite descartável compartilhado entre management command e runserver.
        "NAME": os.getenv("OPSMIND_TEST_DATABASE", ":memory:"),
    }
}
