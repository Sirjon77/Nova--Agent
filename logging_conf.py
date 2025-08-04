import logging, pathlib
pathlib.Path('logs').mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[logging.FileHandler('logs/audit.log'), logging.StreamHandler()]
)
audit_logger = logging.getLogger('audit')
