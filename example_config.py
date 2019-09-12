

class BotConfig:
    prefix = "<your-prefix>"
    name = "<bot-name>"
    icon = "<bot-image-path>"
    token = "<your-token-here>"

    mysql = {
        "host": "localhost",
        "user": "devuser",
        "password": "devpass",
        "db": "devdatabase",
        "charset": "utf8mb4",
        "connect_timeout": 60
    }

    def __getattr__(self, attr):
        return None
