# TODO: this could be configured as a tracer

class Configuration(dict):

    def __init__(self, dictionary: dict, generate_default=False):
        super().__init__(Configuration._configure_dictionary(dictionary, generate_default))
        self.generate_default = generate_default

    @staticmethod
    def _configure_dictionary(dictionary, generate_default):
        for key, value in dictionary.items():
            if isinstance(value, dict):
                dictionary[key] = Configuration(value, generate_default=generate_default)
        return dictionary

    def __getitem__(self, key):
        return super().__getitem__(key)

    def get_config(self, key, default_value=None):
        if self.generate_default and key not in self:
            value = default_value
            if default_value is None:
                value = Configuration({}, self.generate_default)
            self[key] = value
            return value
        return self[key]