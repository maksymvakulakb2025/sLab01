from pathlib import Path

# Дані студента
STUDENT_NAME = "Вакула Максим"
GROUP = "КБ-207"
VARIANT = 5

# Шляхи до файлів
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "lab03.db"
SEED_FILE = DATA_DIR / "seed.json"