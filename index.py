import wfastcgi
wfastcgi.set_fallback_wsgi_handler(__name__)

from application import app as application  # Replace 'app' with the name of your Flask application
