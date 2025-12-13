from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
INFRA_DIR = BASE_DIR / 'infra'

DEFAULT_LOCAL_HOST = 'localhost'
ENV_RUN_IN_DOCKER = 'RUN_IN_DOCKER'
TRUE_VALUE = 'yes'

MIN_SEATS_NUMBER = 1
MAX_SEATS_NUMBER = 24
