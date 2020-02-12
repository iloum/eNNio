import configparser
import os


class ConfigManager:
    def __init__(self, path='.'):
        self._config = configparser.ConfigParser()
        self._config_file = os.path.join(path, "config.ini")

    def get_field(self, field_name, label='GLOBAL'):
        """
        Method to read a field from configuration file
        :param field_name: Name of the field
        :param label: Label under which field resides
        :return: Value of the field
        """
        return self._config[label][field_name]

    def get_all_fields(self, label='GLOBAL'):
        """
        Method to read a field from configuration file
        :param label: Label under which field resides
        :return: Dictionary containing all the configuration
        """
        return self._config[label]

    def set_field(self, field_name, value, label='GLOBAL'):
        """
        Method to write a field to configuration file
        :param field_name: Name of the field
        :param value: Value of the field
        :param label: Label under which field resides
        :return:
        """
        self._config[label][field_name] = value
        self.write_config()

    def _config_file_exists(self):
        return os.path.exists(self._config_file)

    def write_config(self):
        """
        Writes to config file
        """
        with open(self._config_file, 'w') as configuration:
            self._config.write(configuration)

    def read_config(self):
        """
        Reads the config file or creates it if it does not exist
        """
        if not self._config_file_exists():
            self._setup_default_configuration()
            self.write_config()
        else:
            self._config.read(self._config_file)

    def _setup_default_configuration(self):
        """
        Creates default configuration
        Currently sets the language to English
        """
        self._config['GLOBAL'] = {}
        self.set_field(field_name="data-folder",
                       value="data")
        self.set_field(field_name="urls-list-file",
                       value="url_list.csv")
        self.set_field(field_name="db-file-name",
                       value="ennIO.db")

        self._config['VIDEO'] = {}
        self.set_field(field_name="feature-types",
                       value='["lbps", "hogs", "colors", "flow"]',
                       label='VIDEO')
        self.set_field(field_name="resize-width",
                       value="300",
                       label='VIDEO')
        self.set_field(field_name="step",
                       value="3",
                       label='VIDEO')

        self._config['AUDIO'] = {}
        self.set_field(field_name="mid-term-window",
                       value='5',
                       label='AUDIO')
        self.set_field(field_name="mid-term-step",
                       value='0.5',
                       label='AUDIO')
        self.set_field(field_name="short-term-window",
                       value='1',
                       label='AUDIO')
        self.set_field(field_name="short-term-step",
                       value='0.5',
                       label='AUDIO')