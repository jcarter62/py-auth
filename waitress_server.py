from waitress import serve
from os import getenv
import logging
import app

port = getenv('APP_PORT')

logger = logging.getLogger('waitress')
logger.setLevel(logging.DEBUG)

serve(app.app, host='0.0.0.0', port=port)
