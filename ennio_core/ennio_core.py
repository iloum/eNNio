import os
import re
import csv
from config_manager.config_manager import ConfigManager
from data_aquisitor.data_aquisitor import DataAquisitor
from ennio_exceptions import EnnIOException


class EnnIOCore:
    def __init__(self):
        self._config_manager = ConfigManager()
        self._data_aquisitor = DataAquisitor()
        self._video_download_dir = None
        self._url_list_file_location = None

    def setup(self):
        self._config_manager.read_config()
        self._video_download_dir = self._config_manager.get_field('video-download-dir')
        self._url_list_file_location = self._config_manager.get_field('urls-list-file')
        self._data_aquisitor.set_download_location(self._config_manager.get_field('video-download-dir'))

    def construct_model(self):
        """
        Method to create and train an ML model
        :return:
        """
        pass

    def use_model(self, input_file):
        """
        Method to use the existing model in order to predict a
        suitable music score
        :return:
        """
        pass

    def download_video_from_url(self, url):
        """
        Method to download a video file from a youtube URL
        :param url: A youtube video URL
        :return: Downloaded file name
        """
        filename = self._data_aquisitor.download_from_url(url)
        return filename

    def download_video_from_url_file(self):
        """
        Method to download video files from CSV file listing youtube URLs
        :return: List of downloaded file names
        """
        downloaded_videos = list()
        failed_videos = list()
        for row in self._read_url_file():
            try:
                print(row)
                filename = self._data_aquisitor.download_from_url(row['URL'], row['Start'], row['End'])
                downloaded_videos.append(os.path.join(self._video_download_dir, filename))
                #TODO: DB and state stuff
            except EnnIOException:
                failed_videos.append(row)
                continue

        return downloaded_videos, failed_videos

    def get_status(self):
        """
        Method to display systems status
        :return:
        """
        pass

    def extract_features(self, filenames):
        """
        Method to extract audio and video features from files
        :param filenames: List of file names to be used
        :return: Dictionary containing video and audio features
        """
        return {'audio_features': None,
                'video_features': None}

    def _read_url_file(self):
        with open(self._url_list_file_location, encoding='utf-8-sig') as csv_file:
            for row in csv.DictReader(csv_file):
                yield row
