"""WSGI entry point for Render, Railway, Heroku, and Gunicorn deployments."""
from app import create_app

application = create_app()
app = application

if __name__ == "__main__":
    app.run()
