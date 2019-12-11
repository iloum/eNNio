class DataAquisitor:
    def __init__(self):
        self._download_location = None

    def set_download_location(self, path):
        self._download_location = path

    def download_from_url(self, url, start_time=None, end_time=None):
        """
        Method to download youtube videos from a URL list
        :param url: Youtube video URL
        :param start_time: Starting time of the scene
        :param end_time: Ending time of the scene
        :return: filename
        """
        pass

    def download_from_url(self, url, start_time=None, end_time=None):
        """
        Method to download youtube videos from a URL list
        :param url: Youtube video URL
        :param start_time: Starting time of the scene
        :param end_time: Ending time of the scene
        :return: filename
        """
        pass

    def get_metadata(self, filename):
        """
        Method to download video metadata from filename
        :param filename:
        :return: Dictionary of metadata
        """
        pass