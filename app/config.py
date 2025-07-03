from intentkit.config.config import Config as IntentkitConfig


class Config(IntentkitConfig):
    def __init__(self):
        super().__init__()
        self.jwt_secret = self.load("JWT_SECRET")


config = Config()
