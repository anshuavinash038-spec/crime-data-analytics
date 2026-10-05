from flask import request
from flask_login import current_user
from services.database_service import DatabaseService

class ActivityService:
    @classmethod
    def log(cls, action, details=None, user_id=None, user_name=None, user_email=None, ip_address=None):
        """Record audit activity log for administrative or security events."""
        try:
            if user_id is None:
                try:
                    if current_user and current_user.is_authenticated:
                        user_id = current_user.id
                        user_name = current_user.name
                        user_email = current_user.email
                except Exception:
                    pass

            if ip_address is None:
                try:
                    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
                    if ip_address and ',' in ip_address:
                        ip_address = ip_address.split(',')[0].strip()
                except Exception:
                    ip_address = '127.0.0.1'

            query = """
            INSERT INTO activity_logs (user_id, user_name, user_email, action, details, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            DatabaseService.execute_insert(query, (
                user_id,
                user_name or "System",
                user_email or "system@local",
                str(action)[:100],
                str(details) if details else "",
                str(ip_address)[:45] if ip_address else "127.0.0.1"
            ))
        except Exception as e:
            print(f"[ActivityLog Error] Failed to record log: {e}")

    @classmethod
    def get_recent_logs(cls, limit=10):
        query = "SELECT * FROM activity_logs ORDER BY created_at DESC LIMIT %s"
        return DatabaseService.execute_query(query, (int(limit),))

    @classmethod
    def get_all_logs(cls, limit=100, offset=0, action_filter=None):
        query = "SELECT * FROM activity_logs WHERE 1=1"
        params = []
        if action_filter and action_filter.upper() != "ALL":
            query += " AND action = %s"
            params.append(action_filter.strip())
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([int(limit), int(offset)])
        return DatabaseService.execute_query(query, tuple(params))
