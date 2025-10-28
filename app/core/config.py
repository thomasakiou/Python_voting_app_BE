
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
    api_base_url: str 
    # = "https://vmi2848672.contaboserver.net/voting"  # Add this line
    backend_host: str 
    backend_port: str 
    environment: str 


    class Config:
        env_file = ".env"

    # @property
    # def api_base_url(self):
    #     if self.environment == "development":
    #         return f"http://{self.backend_host}:{self.backend_port}/api"
    #     else:
    #         return f"{os.getenv('API_BASE_URL', 'https://vmi2848672.contaboserver.net')}"

    @property
    def db_url(self):
        return (
            f"postgresql://{self.database_username}:{self.database_password}@{self.database_hostname}:{self.database_port}/{self.database_name}"
        )



    # api_prefix: str = "/api"
    @property
    def api_prefix(self) -> str:
        # Always just the relative path for FastAPI
        return ""

    # @property
    # def api_base_url(self) -> str:
    #     # Dynamically generate API base URL depending on environment.
    #     if self.environment == "development":
    #         return f"http://{self.backend_host}:{self.backend_port}/api"
    #     else:
    #         # Uses the domain where the backend is hosted
    #         return f"{os.getenv('API_BASE_URL', 'https://vmi2848672.contaboserver.net')}/api"


settings = Settings()

# Default Super Admin Data
SUPER_ADMIN_USERNAME = "admin"
SUPER_ADMIN_PASSWORD = "123456"
SUPER_ADMIN_FULLNAME="Super Admin"

# Default user password
DEFAULT_VOTER_PASSWORD = "Vote@123"
