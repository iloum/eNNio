import unittest
import os
from unittest.mock import MagicMock
from ennio_core.ennio_core import EnnIOCore

class EnnioCoreSuite(unittest.TestCase):
    def setUp(self):
        self.path = os.path.dirname(os.path.realpath(__file__))

    def tearDown(self):
        if os.path.exists('config.ini'):
            os.remove('config.ini')

    def test_download_video_from_url_file(self):
        ennio_core = EnnIOCore()
        ennio_core.setup()
        ennio_core._url_list_file_location = '../../url_list.csv'
        ennio_core._data_aquisitor.download_from_url = MagicMock(return_value='Pretty Lady')
        ennio_core.download_video_from_url_file()


if __name__ == '__main__':
    unittest.main()
