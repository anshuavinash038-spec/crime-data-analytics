"""
WSGI Entry Point for Production Deployment.
Used by Gunicorn, Waitress, uWSGI, Render, Railway, Heroku, AWS Elastic Beanstalk, etc.
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
