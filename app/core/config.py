from pydantic_settings import BaseSettings

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

    class Config:
        env_file = ".env"
        # env_file_encoding = "utf-8"

    @property
    def db_url(self):
        return (
            f"postgresql://{self.database_username}:{self.database_password}@{self.database_hostname}:{self.database_port}/{self.database_name}"
        )

settings = Settings()



# Default Super Admin Data
SUPER_ADMIN_USERNAME = "admin"
SUPER_ADMIN_PASSWORD = "123456"
SUPER_ADMIN_FULLNAME="Super Admin"

# Default user password
DEFAULT_VOTER_PASSWORD = "Vote@123" 


