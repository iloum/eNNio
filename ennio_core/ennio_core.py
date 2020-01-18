import os
import hashlib
import csv
import multiprocessing
import pandas as pd
import numpy as np
from config_manager.config_manager import ConfigManager
from data_aquisitor.data_aquisitor import DataAquisitor
from ennio_exceptions import VideoAlreadyExist, EnnIOException
from db_manager.db_manager import DbManager
from feature_extractor.video_feature_exractor import VideoFeatureExtractor
from feature_extractor.audio_feature_extractor import AudioFeatureExtractor
# from ml_core.ml_core import MLCore


class EnnIOCore:
    def __init__(self):
        self._config_manager = ConfigManager()
        self._data_aquisitor = DataAquisitor()
        self._db_manager = DbManager()
        self._video_feature_extractor = VideoFeatureExtractor()
        self._audio_feature_extractor = AudioFeatureExtractor()
        # self._ml_core = MLCore()
        self._video_download_dir = None
        self._data_dir = None
        self._url_list_file_location = None
        self._video_stream_dir = None
        self._audio_stream_dir = None
        self._video_feature_names = None
        self._audio_feature_names = None

    def setup(self):
        self._config_manager.read_config()
        self._data_dir = self._config_manager.get_field('data-folder')
        self._video_download_dir = os.path.join(self._data_dir, "downloads")
        parsed_dir = os.path.join(self._video_download_dir, 'parsed')
        self._video_stream_dir = os.path.join(parsed_dir, 'video')
        self._audio_stream_dir = os.path.join(parsed_dir, 'audio')
        self._url_list_file_location = self._config_manager.get_field('urls-list-file')
        self._create_directories()
        self._data_aquisitor.set_download_location(self._video_download_dir)
        self._db_manager.setup(os.path.join(self._data_dir, self._config_manager.get_field('db-file-name')))
        self._video_feature_names = self._db_manager.get_video_feature_names()
        self._audio_feature_names = self._db_manager.get_audio_feature_names()

    def _create_directories(self):
        for directory in [self._audio_stream_dir, self._video_download_dir,
                          self._video_stream_dir]:
            os.makedirs(directory, exist_ok=True)

    def on_exit(self):
        self._db_manager.cleanup()

    # def construct_model(self):
    #     """
    #     Method to create and train an ML model
    #     :return:
    #     """
    #     self.download_video_from_url_file()
    #     self.extract_features(os.listdir(self._video_download_dir))
    #     #TODO: Call MLcore
    #     where_models_will_be_saved = "IN THIS PATH"
    #     self._ml_core.create_model("ANN", where_models_will_be_saved)
    #     # ....
    #     #TODO: To be corrected and changed or tell me what to do... :)

    # def use_model(self, input_file):
    #     """
    #     Method to use the existing model in order to predict a
    #     suitable music score
    #     :return:
    #     """
    #     self.extract_features(input_file)
    #     # TODO: Call MLcore

    def download_video_from_url(self, url):
        """
        Method to download a video file from a youtube URL
        :param url: A youtube video URL
        :return: Downloaded file name
        """
        try:
            return self._download_video_from_entry(url, None, None)
        except EnnIOException:
            return

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
            if self._db_manager.url_exists(url):
                continue
            try:
                file_path = self._download_video_from_entry(url, start_time, end_time)
                downloaded_videos.append(file_path)
            except EnnIOException:
                failed_videos.append(row)
                continue

        return downloaded_videos, failed_videos

    def _download_video_from_entry(self, url, start_time, end_time):
        available_cpus = multiprocessing.cpu_count()
        if available_cpus > 1:
            available_cpus -= 1
        temp = self._data_aquisitor.download_from_url(url,
                                                      start_time=start_time,
                                                      end_time=end_time,
                                                      threads=available_cpus)
        if not temp:
            raise EnnIOException
        metadata = temp[-1]
        video_stream_name = os.path.basename(metadata['filenames'][
                                                 'parsed_video'][-1])
        audio_stream_name = os.path.basename(metadata['filenames'][
                                                 'parsed_audio'][-1])
        video_file_path = os.path.join(self._video_stream_dir,
                                       video_stream_name)
        audio_file_path = os.path.join(self._audio_stream_dir,
                                       audio_stream_name)
        video_stream_id = self._get_id(video_file_path)
        audio_stream_id = self._get_id(audio_file_path)
        start_time = metadata['timestamps'][-1][-1][0]
        end_time = metadata['timestamps'][-1][-1][1]
        self._db_manager.add_audio(audio_id=audio_stream_id,
                                   audio_path=audio_file_path)
        self._db_manager.add_clip(clip_id=video_stream_id,
                                  url=url,
                                  start_time=start_time,
                                  end_time=end_time,
                                  clip_path=video_file_path,
                                  clip_title=video_stream_name,
                                  audio_from_clip=audio_stream_id)
        return video_file_path

    def get_status(self):
        """
        Method to display systems status
        :return:
        """
        print("CLIPS TABLE")
        for entry in self._db_manager.dump_clips():
            print(entry)

        print("AUDIO TABLE")
        for entry in self._db_manager.dump_audio_table():
            print(entry)

    def extract_features(self):
        """
        Method to extract audio and video features from files
        """
        video_features_extracted = []
        audio_features_extracted = []

        for clip in self._db_manager.get_all_clips():
            if not os.path.isfile(clip.clip_path):
                continue
            audio = self._db_manager.get_audio_by_id(clip.audio_from_clip)
            video_features_exist_in_db = clip.video_features != ""
            audio_feature_exist_in_db = audio.audio_features != ""

            if video_features_exist_in_db and audio_feature_exist_in_db:
                continue

            if not video_features_exist_in_db:
                print("Extracting video features from file: {}".format(os.path.basename(clip.clip_path)))
                video_features, self._video_feature_names = \
                    self._video_feature_extractor.extract_video_features(
                        clip.clip_path, ["lbps", "hogs", "colors"])
                clip.video_features = video_features.tostring()
                video_features_extracted.append(clip.clip_path)
                print("Done")

            if not audio_feature_exist_in_db:
                print("Extracting audio features from file: {}".format(os.path.basename(audio.audio_path)))
                audio_features, self._audio_feature_names = \
                    self._audio_feature_extractor.extract_audio_features(
                        audio.audio_path, get_names=True)
                audio.audio_features = audio_features.tostring()
                audio_features_extracted.append(audio.audio_path)
                print("Done")

            self._db_manager.save()

        if video_features_extracted:
            self._db_manager.update_video_feature_names(self._video_feature_names)
        if audio_features_extracted:
            self._db_manager.update_audio_feature_names(self._audio_feature_names)
        self._db_manager.save()

        return video_features_extracted, audio_features_extracted


    def _read_url_file(self):
        with open(self._url_list_file_location, encoding='utf-8-sig') as csv_file:
            for row in csv.DictReader(csv_file):
                yield row

    @staticmethod
    def _get_id(file_path):
        BLOCKSIZE = 65536
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            buf = f.read(BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(BLOCKSIZE)
        return hasher.hexdigest()

    def drop(self, option):
        if option == "audio_features":
            self._db_manager.clear_audio_features()
        if option == "video_features":
            self._db_manager.clear_video_features()

    def create_dataframe_files(self):
        video_features = dict()
        audio_features = dict()
        for clip in self._db_manager.get_all_clips():
            audio = self._db_manager.get_audio_by_id(clip.audio_from_clip)
            video_features_exist_in_db = clip.video_features != ""
            audio_feature_exist_in_db = audio.audio_features != ""

            if video_features_exist_in_db and audio_feature_exist_in_db:
                video_features[clip.clip_id] = np.frombuffer(clip.video_features)
                audio_features[clip.clip_id] = np.frombuffer(audio.audio_features)

        video_df = pd.DataFrame.from_dict(video_features, orient='index',
                                          columns=self._video_feature_names)
        audio_df = pd.DataFrame.from_dict(audio_features, orient='index',
                                          columns=self._audio_feature_names)

        print(video_df)
        print(audio_df)
        video_df.to_pickle(os.path.join(self._data_dir, "video_features.pkl"))
        audio_df.to_pickle(os.path.join(self._data_dir, "audio_features.pkl"))