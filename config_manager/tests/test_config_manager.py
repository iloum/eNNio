import unittest
import os

from config_manager.config_manager import ConfigManager

class ConfigManagerSuite(unittest.TestCase):
    def setUp(self):
        self.path = os.path.dirname(os.path.realpath(__file__))
        self.filename = os.path.join(self.path, "config.ini")

    def tearDown(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def test_no_config_file(self):
        config_manager = ConfigManager(path=self.path)
        config_manager.read_config()
        self.assertTrue(os.path.exists(self.filename))

    def test_set_field(self):
        config_manager = ConfigManager(path=self.path)
        config_manager.read_config()
        config_manager.set_field(field_name="test", value="test")
        self.assertEqual("test", config_manager.get_field(field_name="test"))

    def test_change_value(self):
        config_manager = ConfigManager(path=self.path)
        config_manager.read_config()
        config_manager.set_field(field_name="test", value="test")
        config_manager.set_field(field_name="test", value="test1")
        self.assertEqual("test1", config_manager.get_field(field_name="test"))

if __name__ == '__main__':
    unittest.main()