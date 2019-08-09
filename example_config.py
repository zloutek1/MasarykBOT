
class BotConfig:
    prefix = "<your-prefix>"
    name = "<bot-name>"
    icon = "<bot-image-path>"
    token = "<your-token-here>"

    db_config = {
        "host": "localhost",
        "user": "root",
        "passwd": "",
        "database": "discord",
        "use_unicode": True,
        "autocommit": False
    }

    def __getattr__(self, attr):
        return None
