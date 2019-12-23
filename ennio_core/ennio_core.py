import os
import hashlib
import csv
from config_manager.config_manager import ConfigManager
from data_aquisitor.data_aquisitor import DataAquisitor
from ennio_exceptions import VideoAlreadyExist, EnnIOException
from db_manager.db_manager import DbManager
from feature_extractor.video_feature_exractor import VideoFeatureExtractor
from feature_extractor.audio_feature_extractor import AudioFeatureExtractor
from ml_core.ml_core import MLCore


class EnnIOCore:
    def __init__(self):
        self._config_manager = ConfigManager()
        self._data_aquisitor = DataAquisitor()
        self._db_manager = DbManager()
        self._video_feature_extractor = VideoFeatureExtractor(None) #TODO: Should remove path from constructor
        self._audio_feature_extractor = AudioFeatureExtractor()
        self._ml_core = MLCore(None) #TODO: Should remove path from constructor
        self._video_download_dir = None
        self._url_list_file_location = None
        self._video_stream_dir = None
        self._audio_stream_dir = None

    def setup(self):
        self._config_manager.read_config()
        self._video_download_dir = self._config_manager.get_field('video-download-dir')
        self._video_stream_dir = os.path.join(self._video_download_dir, "video")
        self._audio_stream_dir = os.path.join(self._video_download_dir, "audio")
        self._url_list_file_location = self._config_manager.get_field('urls-list-file')
        self._data_aquisitor.set_download_location(self._config_manager.get_field('video-download-dir'))
        self._db_manager.setup(self._config_manager.get_field('db-file'))
        self._create_directories()

    def _create_directories(self):
        for directory in [self._audio_stream_dir, self._video_download_dir, self._video_stream_dir]:
            os.makedirs(directory, exist_ok=True)

    def on_exit(self):
        self._db_manager.close_db()

    def construct_model(self):
        """
        Method to create and train an ML model
        :return:
        """
        self.download_video_from_url_file()
        self.extract_features(os.listdir(self._video_download_dir))
        #TODO: Call MLcore



    def use_model(self, input_file):
        """
        Method to use the existing model in order to predict a
        suitable music score
        :return:
        """
        self.extract_features(input_file)
        # TODO: Call MLcore

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
            url = row['URL']
            start_time = row['Start']
            end_time = row['End']
            if self._db_manager.is_url_in_db(url):
                continue
            try:
                file_path = self._download_video_from_entry(url, start_time, end_time)
                downloaded_videos.append(file_path)
            except EnnIOException:
                failed_videos.append(row)
                continue

        return downloaded_videos, failed_videos

    def _download_video_from_entry(self, url, start_time, end_time):
        filename = self._data_aquisitor.download_from_url(url, start_time=start_time, end_time=end_time)
        file_path = os.path.join(self._video_download_dir, filename)
        video_id = self._get_video_id(file_path)
        self._db_manager.save_video_data(video_id, filename, file_path, url)
        return file_path

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
        """
        for filename in filenames:
            file_path = os.path.join(self._video_download_dir, filename)
            if not os.path.isfile(file_path):
                continue

            video_id = self._get_video_id(file_path)
            video_features_exist_in_db = self._db_manager.video_features_exist_in_db(video_id)
            audio_feature_exist_in_db = self._db_manager.audio_features_exist_in_db(video_id)

            if video_features_exist_in_db and audio_feature_exist_in_db:
                continue

            if not video_features_exist_in_db:
                video_stream_file_path = os.path.join(self._video_stream_dir, filename)
                video_features, _ = self._video_feature_extractor.extract_video_features(video_stream_file_path)
                self._db_manager.save_video_features(video_id, video_features)

            if not audio_feature_exist_in_db:
                audio_stream_file_path = os.path.join(self._audio_stream_dir, filename)
                audio_features, _ = self._audio_feature_extractor.extract_audio_features(audio_stream_file_path)
                self._db_manager.save_audio_features(video_id, audio_features)

    def _read_url_file(self):
        with open(self._url_list_file_location, encoding='utf-8-sig') as csv_file:
            for row in csv.DictReader(csv_file):
                yield row

    @staticmethod
    def _get_video_id(file_path):
        BLOCKSIZE = 65536
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            buf = f.read(BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(BLOCKSIZE)
        return hasher.hexdigest()
