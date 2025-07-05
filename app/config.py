from intentkit.config.config import Config as IntentkitConfig


class Config(IntentkitConfig):
    def __init__(self):
        super().__init__()
        self.jwt_secret = self.load("JWT_SECRET")
        self.privy_app_id = self.load("PRIVY_APP_ID")
        self.privy_api_key = self.load("PRIVY_API_KEY")


config = Config()
