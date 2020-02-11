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
from ml_core.ml_core import MLCore


class EnnIOCore:
    def __init__(self):
        self._config_manager = ConfigManager()
        self._data_aquisitor = DataAquisitor()
        self._db_manager = DbManager()
        self._video_feature_extractor = VideoFeatureExtractor()
        self._audio_feature_extractor = AudioFeatureExtractor()
        self._ml_core = MLCore()
        self._video_download_dir = None
        self._data_dir = None
        self._url_list_file_location = None
        self._video_stream_dir = None
        self._audio_stream_dir = None
        self._video_feature_names = None
        self._audio_feature_names = None
        self._model_dir = None  # added for models by IL 8/2
        self._predict_results = dict()
        self._video_live_dir = None
        self._video_stream_dir_live = None
        self._evaluation_dir = None
        self._eval_merged_dir = None
        self._eval_video_stream_dir = None

    def setup(self):
        self._config_manager.read_config()
        self._data_dir = self._config_manager.get_field('data-folder')
        self._video_download_dir = os.path.join(self._data_dir, "downloads")
        parsed_dir = os.path.join(self._video_download_dir, 'parsed')
        self._evaluation_dir = os.path.join(self._data_dir, 'evaluation')
        eval_parsed_dir = os.path.join(self._evaluation_dir, 'parsed')
        self._eval_video_stream_dir = os.path.join(eval_parsed_dir, 'video')
        self._eval_merged_dir = os.path.join(self._evaluation_dir, 'merged')
        self._video_stream_dir = os.path.join(parsed_dir, 'video')
        self._audio_stream_dir = os.path.join(parsed_dir, 'audio')
        self._url_list_file_location = self._config_manager.get_field('urls-list-file')
        self._model_dir = os.path.join(self._data_dir, 'models')  # added for models by IL 8/2
        self._video_live_dir = os.path.join(self._data_dir, 'live')  # added for models by IL 8/2
        live_parsed_dir = os.path.join(self._video_live_dir, 'parsed')
        self._video_stream_dir_live = os.path.join(live_parsed_dir, 'video')
        self._create_directories()
        self._data_aquisitor.set_download_location(self._video_download_dir)
        self._db_manager.setup(os.path.join(self._data_dir, self._config_manager.get_field('db-file-name')))
        self._video_feature_names = self._db_manager.get_video_feature_names()
        self._audio_feature_names = self._db_manager.get_audio_feature_names()
        self._check_db_consistency()

    def _create_directories(self):
        for directory in [self._audio_stream_dir, self._video_download_dir,
                          self._video_stream_dir, self._model_dir,
                          self._video_live_dir, self._video_stream_dir_live,
                          self._eval_video_stream_dir, self._eval_merged_dir]:
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

    def construct_models(self):
        """
        Method to create and train an ML model. Instantiates MLCore and creates various models.
        If the models are not trained, then they are trained and saved.
        :return:
        """
        # self.download_video_from_url_file()
        # self.extract_features(os.listdir(self._video_download_dir))
        print("len ", len(self._db_manager.get_all_clips()))
        vid_df, aud_df, met_df = self.create_dataframe_files()
        print(vid_df.shape)
        print(aud_df.shape)
        print(met_df.shape)

        self._ml_core.set_video_dataframe(vid_df)
        self._ml_core.set_audio_dataframe(aud_df)
        self._ml_core.set_metadata_dataframe(met_df)

        self._ml_core.create_models(self._model_dir)

    def audio_video_merge(self, audio_path, video_path, export_path):
        os.system(f"ffmpeg -y -t 60 -i {video_path} -i {audio_path} \
                        -c:v copy -c:a aac -strict experimental {export_path}")

    def merge_results(self, video_path, results):
        """
        uses audio_video_merge from utilities to produce n+1 clips, where n is the number of models
        :param video_path:
        :param results:
        :return: a list of tuples (model, exported_path)
        """
        paths = []
        vid_id = self._db_manager.get_evaluation_clip_by_path(video_path).clip_id
        for result in results:
            print("result ", result)
            audio_id = results[result]
           # print(audio_id)
           # print(self._db_manager.audio_exists(audio_id))
            audio = self._db_manager.get_audio_by_id(audio_id)
            #print(audio)
            audio_path = audio.audio_path
            if result == -1:
                new_name = "Random.mp4"
            else:
                new_name = self._ml_core.get_model_name_from_index(result) + ".mp4"
            export_path = os.path.join(self._eval_merged_dir, new_name)
            self.audio_video_merge(audio_path, video_path, export_path)
            paths.append((vid_id, result, export_path))

        return paths

    def update_evaluation_vote(self,video_id, winner):
        self._db_manager.update_voted_model(video_id, winner)

    def predict_audio_from_models(self, video_df):
        """
        :param video_df:
        :return: the dictionary with the results of all models {model_name: audio_id}
        """
        results = {}
        self.construct_models()
        # load the models

        predictions = self._ml_core.predict(video_df)
        exceptions = []

        for index, clip_id in predictions.items():
            clip = self._db_manager.get_clip_by_id(clip_id)[-1]
            audio = self._db_manager.get_audio_by_id(clip.audio_from_clip)
            if not audio:
                #print("Audio '{}' predicted by model {} does not exist".format(audio_id, index))
                continue
            print("{index}. {audio_id} {audio_path}".format(index=index,
                                                            audio_id=clip.audio_from_clip,
                                                            audio_path=audio.audio_path))
            exceptions.append(clip.audio_from_clip)
            results[index]=clip.audio_from_clip
        results[-1] = self._db_manager.get_random_audio(exceptions)
        print(results)

        return results

    def use_model(self, url, start_time):  # input_file):
        """
        Method to use the existing model in order to predict a
        suitable music score. It assumes that the construct_model above has been called before
        in order to create the models ans store them in a list
        :return:
        """
        # self.extract_features(input_file)

        self.construct_models()

        new_vid_ftrs = self.get_video_features_for_prediction(url, start_time, start_time + 20)

        predictions = self._ml_core.predict(new_vid_ftrs)

        for index, clip_id in predictions.items():
            clip =  self._db_manager.get_clip_by_id(clip_id)[-1]
            audio = self._db_manager.get_audio_by_id(clip.audio_from_clip)
            if not audio:
                print("Audio '{}' predicted by model {} does not exist".format(audio_id, index))
                continue
            print("{index}. {audio_id} {audio_path}".format(index=index,
                                                            audio_id=clip.audio_from_clip,
                                                            audio_path=audio.audio_path))

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
        if clips and mode == "evaluation":
            print("URL already in DB")
            return clips[0].clip_path
        elif clips:
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
        for index, row in self._read_url_file():
            title = row['Film']
            url = row['URL']
            start_time_str = row['Start']
            end_time_str = row['End']
            comment = row['Comment']
            mismatch_url = row['Mismatch URL']
            mismatch_title = row['Mismatch Title']
            start_time = self._time_string_to_seconds(start_time_str)
            end_time = self._time_string_to_seconds(end_time_str)

            while start_time < end_time:
                if not self._clip_exists(url, start_time, start_time + 20):
                    try:
                        file_path = self._download_video_from_entry(url, start_time, start_time + 20,
                                                                    comment=comment,
                                                                    mismatch_title=mismatch_title,
                                                                    mismatch_url=mismatch_url)
                        downloaded_videos.append(file_path)
                    except EnnIOException:
                        failed_videos.add("{index}. {title}, {url}, {start}, "
                                          "{end}, {comment}".format(index=index,
                                                                    title=title,
                                                                    url=url,
                                                                    start=start_time_str,
                                                                    end=end_time_str,
                                                                    comment=comment))
                        break
                start_time += 20

        return downloaded_videos, failed_videos

    def _download_evaluation_video_from_entry(self, url, start_time, end_time):
        """
        Downloads and stores video in Evaluation table
        :param url:
        :param start_time:
        :param end_time:
        :return: the path of downloaded video. this will be used to extract video features
        """
        available_cpus = multiprocessing.cpu_count()
        if available_cpus > 1:
            available_cpus -= 1

        self._data_aquisitor.set_download_location(self._evaluation_dir)
        temp = self._data_aquisitor.download_from_url(url,
                                                      start_time=time.strftime("%M:%S", time.gmtime(start_time)),
                                                      end_time=time.strftime("%M:%S", time.gmtime(end_time)),
                                                      threads=available_cpus)
        self._data_aquisitor.set_download_location(self._video_download_dir)
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

    def _download_video_from_entry(self, url, start_time, end_time, comment="", mismatch_url="", mismatch_title=""):
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
                                      audio_from_clip=audio_stream_id,
                                      mismatch_url=mismatch_url,
                                      mismatch_title=mismatch_title)
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

        video_extractor_kw_args = self._get_video_extractor_config()

        video_features, video_feature_names = self._video_feature_extractor.extract_video_features(video_path,
                                                                                                   **video_extractor_kw_args)
        size = video_features.shape[0]
        video_features_reshaped = video_features.reshape((1, size))
        video_df = pd.DataFrame(video_features_reshaped, columns=video_feature_names)

        return video_features, video_df

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
            index = 1
            for row in csv.DictReader(csv_file):
                index += 1
                yield index, row

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
        metadata_columns = ['Title', 'Url', 'Video file path', 'Audio file path', 'Mismatch Title', 'Mismatch URL']
        for clip in self._db_manager.get_all_clips():
            audio = self._db_manager.get_audio_by_id(clip.audio_from_clip)
            video_features_exist_in_db = clip.video_features != ""
            audio_feature_exist_in_db = audio.audio_features != ""

            if video_features_exist_in_db and audio_feature_exist_in_db:
                video_features[clip.clip_id] = np.frombuffer(clip.video_features)
                audio_features[clip.clip_id] = np.frombuffer(audio.audio_features)
                metadata[clip.clip_id] = [clip.clip_title, clip.url, clip.clip_path, audio.audio_path,
                                          clip.mismatch_title, clip.mismatch_url]

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

        return video_df, audio_df, metadata_df

    def get_video_features_for_prediction(self, url, start_time, end_time):
        '''
        Method to get the features for an external video for processing
        :param path:
        :return:
        '''

        available_cpus = multiprocessing.cpu_count()
        if available_cpus > 1:
            available_cpus -= 1

        self._data_aquisitor.set_download_location(self._video_live_dir)
        temp = self._data_aquisitor.download_from_url(url,
                                                      start_time=time.strftime("%M:%S", time.gmtime(start_time)),
                                                      end_time=time.strftime("%M:%S", time.gmtime(end_time)),
                                                      threads=available_cpus)
        self._data_aquisitor.set_download_location(self._video_download_dir)
        if not temp:
            raise EnnIOException
        metadata = temp[-1]
        video_stream_name = os.path.basename(metadata['filenames'][
                                                 'parsed_video'][-1])

        video_file_path = os.path.join(self._video_stream_dir_live,
                                       video_stream_name)

        video_extractor_kw_args = self._get_video_extractor_config()
        video_features, video_feature_names = self._video_feature_extractor.extract_video_features(video_file_path,
                                                                                                   **video_extractor_kw_args)

        size = video_features.shape[0]
        video_features_reshaped = video_features.reshape((1, size))
        # print(size)
        # print(type(video_features_reshaped))

        video_df = pd.DataFrame(video_features_reshaped, columns=video_feature_names)

        return video_df

    @staticmethod
    def _time_string_to_seconds(time_string):
        return reduce(lambda x, y: x + y, [int(x) * (60 ** i) for i, x in enumerate(time_string.split(":")[::-1])])

    def _clip_exists(self, url, start_time, end_time):
        clips = self._db_manager.get_clips_by_url(url)
        for clip in clips:
            if clip.start_time == start_time and clip.end_time == end_time:
                return True
        return False
