from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
INFRA_DIR = BASE_DIR / 'infra'

DEFAULT_LOCAL_HOST = 'localhost'
ENV_RUN_IN_DOCKER = 'RUN_IN_DOCKER'
TRUE_VALUE = 'yes'

LOGS_DIR = Path('logs')
LOG_FILE = LOGS_DIR / 'app.log'
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 МБ
LOG_BACKUP_COUNT = 10
