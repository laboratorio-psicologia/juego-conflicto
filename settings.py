from os import environ

SESSION_CONFIGS = [
    dict(
        name='juego_conflicto',
        display_name='Juego Conflicto – Bots (6 jugadores, 8 rondas)',
        app_sequence=['juego_conflicto'],
        num_demo_participants=6,
        use_browser_bots=True,
    ),
    dict(
        name='juego_manual',
        display_name='Juego Conflicto – Manual / Debug (6 jugadores, 8 rondas)',
        app_sequence=['juego_conflicto'],
        num_demo_participants=6,
        use_browser_bots=False,
    ),
    dict(
        name='juego_solo',
        display_name='Juego Conflicto – Vista jugador único (2 rondas)',
        app_sequence=['juego_conflicto'],
        num_demo_participants=6,
        use_browser_bots=False,
        is_solo=True,
        solo_rounds=2,
    ),
]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00,
    participation_fee=0.00,
    doc="",
)

PARTICIPANT_FIELDS = ['acumulado']
SESSION_FIELDS = []

LANGUAGE_CODE = 'es'
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True
POINTS_CUSTOM_NAME = 'fichas'

ROOMS = []

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD', 'admin1234')

DEMO_PAGE_INTRO_HTML = ""

SECRET_KEY = environ.get('DJANGO_SECRET_KEY', 'dev-insecure-key-cambiar-en-produccion')

# Heroku: Postgres via DATABASE_URL (oTree lo detecta automáticamente)
# En local usa SQLite por defecto, no hace falta configurarlo
