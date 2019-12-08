import configparser
import os

class ConfigManager:
    def __init__(self, path='.'):
        self.config = configparser.ConfigParser()
        self.config_file = os.path.join(path, "config.ini")

    def get_field(self, field_name, label='GLOBAL'):
        """
        Method to read a field from configuration file
        :param field_name: Name of the field
        :param label: Label under which field resides
        :return: Value of the field
        """
        return self.config[label][field_name]

    def set_field(self, field_name, value, label='GLOBAL'):
        """
        Method to write a field to configuration file
        :param field_name: Name of the field
        :param value: Value of the field
        :param label: Label under which field resides
        :return:
        """
        self.config[label][field_name] = value
        self.write_config()

    def _config_file_exists(self):
        return os.path.exists(self.config_file)

    def write_config(self):
        """
        Writes to config file
        """
        with open(self.config_file, 'w') as configuration:
            self.config.write(configuration)

    def read_config(self):
        """
        Reads the config file or creates it if it does not exist
        """
        if not self._config_file_exists():
            self._setup_default_configuration()
            self.write_config()
        else:
            self.config.read(self.config_file)

    def _setup_default_configuration(self):
        """
        Creates default configuration
        Currently sets the language to English
        """
        self.config['GLOBAL'] = {}
        self.set_field(field_name="urls-list-file",
                       value="data/urls.csv")
        self.set_field(field_name="ml-model-file",
                       value="data/model.sav")
        self.set_field(field_name="db-file",
                       value="data/ennIO.db")
        self.set_field(field_name="video-download-dir",
                       value="data/downloads/")
        self.set_field(field_name="output-dir",
                       value="data/output/")