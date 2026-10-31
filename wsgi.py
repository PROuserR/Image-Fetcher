"""Production entry point.

    gunicorn wsgi:app
    PythonAnywhere:  from wsgi import application
"""
from imagefetcher import create_app

app = application = create_app()
