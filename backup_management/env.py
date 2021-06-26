import os

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
PROXY = os.environ.get('PROXY')

DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = 'BackupManagement'
MAIL_TO = os.environ.get('MAIL_TO')

DEBUG = False
ALLOWED_HOSTS = ['127.0.0.1']
TIME_ZONE = 'Asia/Ho_Chi_Minh'
MEMCACHED = '127.0.0.1:11211'

CRONJOB = '0 7 * * *'
VIEWER_PASS = os.environ.get('VIEWER_PASS')
