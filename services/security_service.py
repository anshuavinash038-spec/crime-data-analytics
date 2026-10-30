import re
from datetime import datetime, timedelta
from services.database_service import DatabaseService
from services.activity_service import ActivityService

# Common insecure and basic passwords that should be rejected
COMMON_BASIC_PASSWORDS = {
    "123456", "12345678", "123456789", "1234567890", "password", "password123",
    "admin123", "admin@123", "user123", "qwerty", "qwertyuiop", "letmein",
    "welcome", "welcome123", "pass1234", "password1", "crime123", "india123",
    "111111", "000000", "123123", "654321", "iloveyou", "monkey", "dragon",
    "football", "master", "shadow", "sunshine", "princess", "superman", "batman",
    "secret", "abc123", "abcdef", "testing123", "login123", "root123"
}

PASSWORD_EXAMPLES = [
    "Crime#Safe2026",
    "Avinash@Secure99",
    "Cyber$Guard#24",
    "India#Shield@26",
    "Data*Protect!8"
]

class SecurityService:
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_MINUTES = 4

    @classmethod
    def validate_gmail(cls, email: str):
        """
        Enforce strict validation that email ends with @gmail.com.
        """
        if not email or not isinstance(email, str):
            return False, "Email address is required."
        
        email = email.strip().lower()
        # Ensure proper RFC-compliant gmail username structure before @gmail.com
        gmail_pattern = r'^[a-zA-Z0-9]+([._%+-][a-zA-Z0-9]+)*@gmail\.com$'
        
        if not re.match(gmail_pattern, email):
            if not email.endswith('@gmail.com'):
                return False, "Only @gmail.com email addresses are allowed (e.g., yourname@gmail.com)."
            return False, "Please enter a valid @gmail.com email address format."
        
        return True, ""

    @classmethod
    def validate_password_strength(cls, password: str, name: str = None, email: str = None):
        """
        Enforce strong password policy and reject basic/common passwords.
        Criteria:
        - Minimum 8 characters long
        - At least 1 uppercase letter (A-Z)
        - At least 1 lowercase letter (a-z)
        - At least 1 number (0-9)
        - At least 1 special character (!@#$%^&*...)
        - Not in common basic password blacklist
        - Not containing user's name or email username if >= 3 characters
        """
        if not password or not isinstance(password, str):
            return False, "Password is required."

        if len(password) < 8:
            return False, "Password must be at least 8 characters long."

        if not re.search(r'[A-Z]', password):
            return False, "Password must include at least one UPPERCASE letter (A-Z)."

        if not re.search(r'[a-z]', password):
            return False, "Password must include at least one LOWERCASE letter (a-z)."

        if not re.search(r'[0-9]', password):
            return False, "Password must include at least one NUMBER (0-9)."

        if not re.search(r'[!@#$%^&*(),.?":{}|<>_+\-=\[\]\\/;~`]', password):
            return False, "Password must include at least one SPECIAL CHARACTER (e.g. @, #, $, %, &, *)."

        pwd_lower = password.lower()
        if pwd_lower in COMMON_BASIC_PASSWORDS:
            return False, "Basic or commonly used passwords are not allowed. Please choose a more secure password."

        # Check if password is too trivial like repeated characters or sequences
        if len(set(password)) < 4:
            return False, "Password cannot consist of repeated or trivial characters."

        # Check if password is identically equal to name or email handle
        if name and pwd_lower == name.strip().lower():
            return False, "Password cannot be exactly identical to your full name."

        if email and '@' in email:
            email_handle = email.split('@')[0].lower()
            if pwd_lower == email_handle:
                return False, "Password cannot be identical to your email handle."

        return True, ""

    @classmethod
    def check_lockout(cls, email: str):
        """
        Check if account or email is currently locked due to 5 failed attempts.
        Returns: (is_locked: bool, error_message: str, seconds_remaining: int)
        """
        if not email:
            return False, "", 0
        
        email_clean = email.strip().lower()
        try:
            record = DatabaseService.execute_query(
                "SELECT failed_attempts, locked_until FROM login_security WHERE email = %s",
                (email_clean,),
                fetch_one=True
            )
            if not record:
                return False, "", 0

            locked_until_val = record.get("locked_until")
            if locked_until_val:
                locked_until_dt = None
                if isinstance(locked_until_val, str):
                    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
                        try:
                            locked_until_dt = datetime.strptime(locked_until_val[:19], "%Y-%m-%d %H:%M:%S")
                            break
                        except ValueError:
                            continue
                elif isinstance(locked_until_val, datetime):
                    locked_until_dt = locked_until_val

                if locked_until_dt and locked_until_dt > datetime.now():
                    diff = locked_until_dt - datetime.now()
                    total_secs = max(1, int(diff.total_seconds()))
                    mins = total_secs // 60
                    secs = total_secs % 60
                    time_display = f"{mins}m {secs}s" if mins > 0 else f"{secs} seconds"
                    return True, f"System is blocked for {cls.LOCKOUT_MINUTES} minutes due to 5 failed attempts. Time remaining: {time_display}. You cannot perform any action until time finishes.", total_secs
                else:
                    # Lockout expired, auto-reset
                    cls.clear_failed_attempts(email_clean)
                    return False, "", 0

            return False, "", 0
        except Exception as e:
            print(f"[SecurityService Warning] Lockout check error: {e}")
            return False, "", 0

    @classmethod
    def record_failed_attempt(cls, email: str, ip_address: str = None):
        """
        Track failed password attempts.
        - Attempt 1, 2: Standard error message.
        - Attempt 3: Warning "Only 2 attempts remaining".
        - Attempt 4: Warning "Only 1 attempt remaining".
        - Attempt 5: Block/Lockout for exactly 4 minutes.
        Returns: (is_locked: bool, feedback_message: str, seconds_remaining: int)
        """
        if not email:
            return False, "Invalid email address or password.", 0

        email_clean = email.strip().lower()
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        try:
            record = DatabaseService.execute_query(
                "SELECT id, failed_attempts, locked_until FROM login_security WHERE email = %s",
                (email_clean,),
                fetch_one=True
            )

            if record:
                attempts = int(record.get("failed_attempts", 0)) + 1
                if attempts >= cls.MAX_FAILED_ATTEMPTS:
                    lock_time = now + timedelta(minutes=cls.LOCKOUT_MINUTES)
                    lock_str = lock_time.strftime("%Y-%m-%d %H:%M:%S")
                    DatabaseService.execute_query(
                        "UPDATE login_security SET failed_attempts = %s, locked_until = %s, last_failed_at = %s WHERE email = %s",
                        (attempts, lock_str, now_str, email_clean),
                        fetch_all=False
                    )
                    ActivityService.log(
                        "Account Blocked (4 Min)",
                        f"Account {email_clean} blocked for {cls.LOCKOUT_MINUTES} mins after {attempts} consecutive failed login attempts",
                        user_email=email_clean,
                        ip_address=ip_address
                    )
                    total_secs = cls.LOCKOUT_MINUTES * 60
                    return True, f"System is blocked for {cls.LOCKOUT_MINUTES} minutes due to 5 consecutive failed login attempts. Time remaining: {cls.LOCKOUT_MINUTES}m 00s. Please wait until the timer finishes.", total_secs
                else:
                    DatabaseService.execute_query(
                        "UPDATE login_security SET failed_attempts = %s, last_failed_at = %s WHERE email = %s",
                        (attempts, now_str, email_clean),
                        fetch_all=False
                    )
                    remaining = cls.MAX_FAILED_ATTEMPTS - attempts
                    if attempts >= 3:
                        msg = f"Invalid email address or password. Warning: Only {remaining} attempt(s) remaining before system lockout!"
                    else:
                        msg = "Invalid email address or password. Please try again."
                    return False, msg, 0
            else:
                DatabaseService.execute_insert(
                    "INSERT INTO login_security (email, failed_attempts, locked_until, last_failed_at) VALUES (%s, %s, NULL, %s)",
                    (email_clean, 1, now_str)
                )
                return False, "Invalid email address or password. Please try again.", 0
        except Exception as e:
            print(f"[SecurityService Error] Failed to record login attempt: {e}")
            return False, "Invalid email address or password. Please try again.", 0

    @classmethod
    def clear_failed_attempts(cls, email: str):
        """Reset failed attempt counters upon successful authentication or password reset."""
        if not email:
            return
        email_clean = email.strip().lower()
        try:
            DatabaseService.execute_query(
                "UPDATE login_security SET failed_attempts = 0, locked_until = NULL WHERE email = %s",
                (email_clean,),
                fetch_all=False
            )
        except Exception as e:
            print(f"[SecurityService Notice] Clear attempts notice: {e}")

    @classmethod
    def get_password_examples(cls):
        """Return list of suggested strong passwords."""
        return PASSWORD_EXAMPLES
