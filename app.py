import os
from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from services.database_service import DatabaseService
from models.user_model import User

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.auto_reload = True
    Config.init_app(app)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(user_id)

    # Initialize Database Schema & Seed Data on Start
    with app.app_context():
        try:
            DatabaseService.init_db()
            app.logger.info("[App Startup] Database schema initialized and verified successfully.")
        except Exception as e:
            app.logger.error(f"[App Startup Error] Critical failure during DB initialization: {e}", exc_info=True)
            print(f"[FATAL DB INIT ERROR] {e}")

    # Register Blueprints
    from routes.auth_routes import auth_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.crime_routes import crime_bp
    from routes.analysis_routes import analysis_bp
    from routes.visualization_routes import visualization_bp
    from routes.search_routes import search_bp
    from routes.reports_routes import reports_bp
    from routes.powerbi_routes import powerbi_bp
    from routes.admin_routes import admin_bp
    from routes.api_routes import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(crime_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(visualization_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(powerbi_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Error Handlers
    @app.errorhandler(403)
    def access_forbidden(e):
        return render_template('403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    # Reverse Proxy support for Production (Render, Railway, Heroku, Nginx)
    try:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    except Exception:
        pass

    # Security Headers & Cache control
    @app.after_request
    def set_security_headers(response):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        return response

    return app

app = create_app()

if __name__ == '__main__':
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')

    print("=" * 60)
    print(" Crime Data Analytics and Visualization System")
    print(" National Crime Intelligence & Area Portal")
    print(f" Server running on http://{host}:{port} (Debug: {debug})")
    print("=" * 60)
    app.run(host=host, port=port, debug=debug)

