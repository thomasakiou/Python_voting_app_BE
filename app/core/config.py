from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    api_base_url: str = "http://localhost:8000/api"
    backend_host: str = "localhost"
    backend_port: str = "8000"
    environment: str = "development"

    # SMTP (Email) settings
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_sender_email: str = ""

    # Twilio (SMS) settings
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    # OTP settings
    otp_expire_minutes: int = 10

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def db_url(self):
        return (
            f"postgresql://{self.database_username}:{self.database_password}@{self.database_hostname}:{self.database_port}/{self.database_name}"
        )

    @property
    def api_prefix(self) -> str:
        # Always just the relative path for FastAPI
        return ""

settings = Settings()

# Default Super Admin Data
SUPER_ADMIN_USERNAME = "admin"
SUPER_ADMIN_PASSWORD = "123456"
SUPER_ADMIN_FULLNAME = "Super Admin"

# Default user password
DEFAULT_VOTER_PASSWORD = "Vote@123"
