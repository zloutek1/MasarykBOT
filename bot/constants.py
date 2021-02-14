import yaml

with open('config.yml', encoding="UTF-8") as f:
    _CONFIG_YAML = yaml.safe_load(f)

class YAMLGetter(type):
    """
    This is a metaclass that allows the subclass to access
    the configuration data by class attributes.

    Example usage:
        # config.yml
        bot:
            prefix: "!"

        # config.py
        class Config(metaclass=YAMLGetter):
            pass

        # useage in python code
        >> from config import Config
        >> Config.bot
        {prefix: "!"}
    """

    def __getattr__(cls, key):
        val = _CONFIG_YAML.get(key)
        if isinstance(val, (list, dict)):
            return cls(val) # initiate subclass
        return val

class YAMLIterator:
    """
    This is an iterator class that returns that wraps a
    cls instance around the iterated collection
    """

    def __init__(self, cls, iterable):
        self.cls = cls
        self.iterable = iterable
        self.index = 0

    def __next__(self):
        if self.index < len(self.iterable):
            val = self.iterable[self.index]
            self.index += 1
            return self.cls(val)
        raise StopIteration

class Config(metaclass=YAMLGetter):
    """
    This is a class that allows access to
    the configuration data by class attributes.

    The initial getting of the attribute is handeled by the
    metaclass.

    Example usage:
        # config.yml
        bot:
            prefix: "!"

        # useage in python code
        >> from config import Config
        >> Config.bot.prefix
        "!"
    """

    def __init__(self, config):
        self.config = config

    def __getattr__(self, key):
        if isinstance(self.config, dict):
            val = self.config.get(key)
            if isinstance(val, (list, dict)):
                return Config(val)
            return val
        elif isinstance(self.config, list):
            for elem in self.config:
                val = elem.get(key)
                if isinstance(val, (list, dict)):
                    return Config(val)
                if val:
                    return val

    def __iter__(self):
        return YAMLIterator(self.__class__, self.config)

    def __repr__(self):
        return f"Config({self.config})"