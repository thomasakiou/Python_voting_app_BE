from pydantic_settings import BaseSettings
import os

# # Escape special characters in password
# from urllib.parse import quote_plus


class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int


    backend_host: str = "localhost"
    backend_port: str = "8000"
    environment: str = "development"  # "production" or "development"


    class Config:
        env_file = ".env"
        # env_file_encoding = "utf-8"

    @property
    def db_url(self):
        return (
            f"postgresql://{self.database_username}:{self.database_password}@{self.database_hostname}:{self.database_port}/{self.database_name}"
        )

    # api_prefix: str = "/api"
    @property
    def api_prefix(self) -> str:
        # Always just the relative path for FastAPI
        return "/api"

    @property
    def api_base_url(self) -> str:
        # Dynamically generate API base URL depending on environment.
        if self.environment == "development":
            return f"http://{self.backend_host}:{self.backend_port}/api"
        else:
            # Uses the domain where the backend is hosted
            return f"{os.getenv('API_BASE_URL', 'https://yourdomain.com')}/api"

settings = Settings()


# Default Super Admin Data
SUPER_ADMIN_USERNAME = "admin"
SUPER_ADMIN_PASSWORD = "123456"
SUPER_ADMIN_FULLNAME="Super Admin"

# Default user password
DEFAULT_VOTER_PASSWORD = "Vote@123" 


