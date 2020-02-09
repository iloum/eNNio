import os
import hashlib
import csv
import multiprocessing
import time
import pandas as pd
import numpy as np
from config_manager.config_manager import ConfigManager
from data_aquisitor.data_aquisitor import DataAquisitor
from ennio_exceptions import VideoAlreadyExist, EnnIOException
from db_manager.db_manager import DbManager
from feature_extractor.video_feature_exractor import VideoFeatureExtractor
from feature_extractor.audio_feature_extractor import AudioFeatureExtractor
from functools import reduce


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
        self._eval_video_stream_dir = None
        self._video_stream_dir = None
        self._audio_stream_dir = None
        self._video_feature_names = None
        self._audio_feature_names = None

    def setup(self):
        self._config_manager.read_config()
        self._data_dir = self._config_manager.get_field('data-folder')
        self._video_download_dir = os.path.join(self._data_dir, "downloads")
        parsed_dir = os.path.join(self._video_download_dir, 'parsed')
        evaluation_dir = os.path.join(self._video_download_dir, 'evaluation')
        self._eval_video_stream_dir = os.path.join(evaluation_dir, 'video')
        self._video_stream_dir = os.path.join(parsed_dir, 'video')
        self._audio_stream_dir = os.path.join(parsed_dir, 'audio')
        self._url_list_file_location = self._config_manager.get_field('urls-list-file')
        self._create_directories()
        self._data_aquisitor.set_download_location(self._video_download_dir)
        self._db_manager.setup(os.path.join(self._data_dir, self._config_manager.get_field('db-file-name')))
        self._video_feature_names = self._db_manager.get_video_feature_names()
        self._audio_feature_names = self._db_manager.get_audio_feature_names()
        self._check_db_consistency()

    def _create_directories(self):
        for directory in [self._audio_stream_dir, self._video_download_dir,
                          self._video_stream_dir]:
            os.makedirs(directory, exist_ok=True)

    def _check_db_consistency(self):
        print("Checking DB consistency")
        removed_clips = []
        for clip in self._db_manager.get_all_clips():
            if not os.path.exists(clip.clip_path):
                audio = self._db_manager.get_audio_by_id(clip.audio_from_clip)
                if audio:
                    self._db_manager.remove_audio(audio)
                self._db_manager.remove_clip(clip)
                removed_clips.append(clip)

        for audio in self._db_manager.get_all_audio():
            if not os.path.exists(audio.audio_path):
                clip = self._db_manager.get_clip_by_audio_id(audio.audio_id)
                self._db_manager.remove_audio(audio)
                if clip:
                    self._db_manager.remove_clip(clip)
                    removed_clips.append(clip)

        if removed_clips:
            print("Following clip files are missing:")
            for index, clip in enumerate(removed_clips, start=1):
                print("\t{index}. {url} {path}".format(index=index,
                                                       url=clip.url,
                                                       path=clip.clip_path))

            print("Please download them again if needed")
        print("Done")

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

    def download_video_from_url(self, url, start_time_str, mode="training"):
        """
        Method to download a video file from a youtube URL
        :param mode: default value "training" so as not to interfere with already functionality
        :param url: A youtube video URL
        :param start_time_str: Clip start time
        :return: Downloaded file name
        """
        if mode == "evaluation":
            clips = self._db_manager.get_evaluation_clips_by_url(url)
        else:
            clips = self._db_manager.get_clips_by_url(url)
        if clips:
            print("URL already in DB")
            return
        if start_time_str:
            start_time = self._time_string_to_seconds(start_time_str)
        else:
            start_time = 0
        try:
            if mode == "evaluation":
                path = self._download_evaluation_video_from_entry(url, start_time,
                                                                  start_time + 20)
            else:
                path = self._download_video_from_entry(url, start_time,
                                                       start_time + 20)
            return path
        except EnnIOException:
            return

    def download_video_from_url_file(self):
        """
        Method to download video files from CSV file listing youtube URLs
        :return: List of downloaded file names
        """
        downloaded_videos = list()
        failed_videos = set()
        for row in self._read_url_file():
            title = row['Film']
            url = row['URL']
            start_time_str = row['Start']
            end_time_str = row['End']
            comment = row['Comment']
            start_time = self._time_string_to_seconds(start_time_str)
            end_time = self._time_string_to_seconds(end_time_str)

            while start_time < end_time:
                if not self._clip_exists(url, start_time, start_time + 20):
                    try:
                        file_path = self._download_video_from_entry(url, start_time, start_time + 20, comment=comment)
                        downloaded_videos.append(file_path)
                    except EnnIOException:
                        failed_videos.add("{title}, {url}, {start}, {end}, {comment}".format(title=title,
                                                                                             url=url,
                                                                                             start=start_time_str,
                                                                                             end=end_time_str,
                                                                                             comment=comment))
                start_time += 20

        return downloaded_videos, failed_videos

    def _download_evaluation_video_from_entry(self, url, start_time, end_time, comment=""):
        available_cpus = multiprocessing.cpu_count()
        if available_cpus > 1:
            available_cpus -= 1

        temp = self._data_aquisitor.download_from_url(url,
                                                      start_time=time.strftime("%M:%S", time.gmtime(start_time)),
                                                      end_time=time.strftime("%M:%S", time.gmtime(end_time)),
                                                      threads=available_cpus)
        if not temp:
            raise EnnIOException
        metadata = temp[-1]
        video_stream_name = os.path.basename(metadata['filenames'][
                                                 'parsed_video'][-1])
        # audio_stream_name = os.path.basename(metadata['filenames'][
        #                                         'parsed_audio'][-1])
        video_file_path = os.path.join(self._eval_video_stream_dir,
                                       video_stream_name)
        # audio_file_path = os.path.join(self._audio_stream_dir,
        #                               audio_stream_name)
        video_stream_id = self._get_id(video_file_path)
        # audio_stream_id = self._get_id(audio_file_path)
        # if not self._db_manager.audio_exists(audio_stream_id):
        #    self._db_manager.add_audio(audio_id=audio_stream_id,
        #                               audio_path=audio_file_path)
        if not self._db_manager.evaluation_video_exists(video_stream_id):
            self._db_manager.add_evaluation_clip(clip_id=video_stream_id,
                                                 url=url,
                                                 start_time=start_time,
                                                 end_time=end_time,
                                                 clip_path=video_file_path,
                                                 clip_title=video_stream_name)
        return video_file_path

    def _download_video_from_entry(self, url, start_time, end_time, comment=""):
        available_cpus = multiprocessing.cpu_count()
        if available_cpus > 1:
            available_cpus -= 1

        temp = self._data_aquisitor.download_from_url(url,
                                                      start_time=time.strftime("%M:%S", time.gmtime(start_time)),
                                                      end_time=time.strftime("%M:%S", time.gmtime(end_time)),
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
        if not self._db_manager.audio_exists(audio_stream_id):
            self._db_manager.add_audio(audio_id=audio_stream_id,
                                       audio_path=audio_file_path)
        if not self._db_manager.video_exists(video_stream_id):
            self._db_manager.add_clip(clip_id=video_stream_id,
                                      url=url,
                                      start_time=start_time,
                                      end_time=end_time,
                                      clip_path=video_file_path,
                                      clip_title=video_stream_name,
                                      clip_description=comment,
                                      audio_from_clip=audio_stream_id)
        return video_file_path

    def get_status(self):
        """
        Method to display systems status
        :return:
        """
        print("CLIPS TABLE")
        print("Number of video clips in the db: {}".format(len(self._db_manager.dump_clips()) - 1))
        print()

        print("AUDIO TABLE")
        print("Number of audio clips in the db: {}".format(len(self._db_manager.dump_audio_table()) - 1))

    def _get_video_extractor_config(self):
        config = self._config_manager.get_all_fields(label='VIDEO')
        return {"ftlist": eval(config["feature-types"]),
                "width": int(config["resize-width"]),
                "step": int(config["step"])}

    def _get_audio_extractor_config(self):
        config = self._config_manager.get_all_fields(label='AUDIO')
        return {"mid_window": float(config["mid-term-window"]),
                "mid_step": float(config["mid-term-step"]),
                "short_window": float(config["short-term-window"]),
                "short_step": float(config["short-term-step"])}

    def extract_video_features_for_evaluation(self, video_path):
        """
        Method to extract video features and store in Evaluation table
        :return: extracted video features
        """
        video_features_extracted = []
        video_extractor_kw_args = self._get_video_extractor_config()

        for clip in self._db_manager.get_all_evaluation_clips():
            if clip.clip_path == video_path:
                video_features_exist_in_db = clip.video_features != ""

                if video_features_exist_in_db:
                    continue

                if not video_features_exist_in_db:
                    print("Extracting video features from file: {}".format(os.path.basename(clip.clip_path)))
                    video_features, self._video_feature_names = \
                        self._video_feature_extractor.extract_video_features(
                            clip.clip_path, **video_extractor_kw_args)
                    clip.video_features = video_features.tostring()
                    video_features_extracted.append(clip.clip_path)
                    print("Done")

                self._db_manager.save()

            if video_features_extracted:
                self._db_manager.update_video_feature_names(self._video_feature_names)

        return video_features_extracted

    def extract_features(self):
        """
        Method to extract audio and video features from files
        """
        video_features_extracted = []
        audio_features_extracted = []
        video_extractor_kw_args = self._get_video_extractor_config()
        audio_extractor_kw_args = self._get_audio_extractor_config()

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
                        clip.clip_path, **video_extractor_kw_args)
                clip.video_features = video_features.tostring()
                video_features_extracted.append(clip.clip_path)
                print("Done")

            if not audio_feature_exist_in_db:
                print("Extracting audio features from file: {}".format(os.path.basename(audio.audio_path)))
                audio_features, self._audio_feature_names = \
                    self._audio_feature_extractor.extract_audio_features(
                        audio.audio_path, **audio_extractor_kw_args)
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
        """
        Method to clear DB tables or attributes
        :param option: String
        """
        if option == "audio_features":
            self._db_manager.clear_audio_features()
        if option == "video_features":
            self._db_manager.clear_video_features()
        if option == "tables":
            self._db_manager.clear_audio_table()
            self._db_manager.clear_clips_table()

    def create_dataframe_files(self):
        video_features = dict()
        audio_features = dict()
        metadata = dict()
        metadata_columns = ['Title', 'Url', 'Video file path', 'Audio file path']
        for clip in self._db_manager.get_all_clips():
            audio = self._db_manager.get_audio_by_id(clip.audio_from_clip)
            video_features_exist_in_db = clip.video_features != ""
            audio_feature_exist_in_db = audio.audio_features != ""

            if video_features_exist_in_db and audio_feature_exist_in_db:
                video_features[clip.clip_id] = np.frombuffer(clip.video_features)
                audio_features[clip.clip_id] = np.frombuffer(audio.audio_features)
                metadata[clip.clip_id] = [clip.clip_title, clip.url, clip.clip_path, audio.audio_path]

        video_df = pd.DataFrame.from_dict(video_features, orient='index',
                                          columns=self._video_feature_names)
        audio_df = pd.DataFrame.from_dict(audio_features, orient='index',
                                          columns=self._audio_feature_names)
        metadata_df = pd.DataFrame.from_dict(metadata, orient='index',
                                             columns=metadata_columns)

        options_str = str(self._get_video_extractor_config()).replace(" ", "").replace("'", "").replace(":", "_")
        video_features_file = "video_features_df_{options}.pkl".format(options=options_str)
        video_df.to_pickle(os.path.join(self._data_dir,
                                        video_features_file))
        print("Saved to {file_name}".format(file_name=video_features_file))

        options_str = str(self._get_audio_extractor_config()).replace(" ", "").replace("'", "").replace(":", "_")
        audio_features_file = "audio_features_df_{options}.pkl".format(options=options_str)
        audio_df.to_pickle(os.path.join(self._data_dir,
                                        audio_features_file))
        print("Saved to {file_name}".format(file_name=audio_features_file))

        metadata_file = "metadata_df.pkl"
        metadata_df.to_pickle(os.path.join(self._data_dir, metadata_file))
        print("Saved to {file_name}".format(file_name=metadata_file))

    @staticmethod
    def _time_string_to_seconds(time_string):
        return reduce(lambda x, y: x + y, [int(x) * (60 ** i) for i, x in enumerate(time_string.split(":")[::-1])])

    def _clip_exists(self, url, start_time, end_time):
        clips = self._db_manager.get_clips_by_url(url)
        for clip in clips:
            if clip.start_time == start_time and clip.end_time == end_time:
                return True
        return False
