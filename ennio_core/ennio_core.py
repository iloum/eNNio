import os
import hashlib
import csv
import multiprocessing
import time
import pandas as pd
import numpy as np
import shutil
from config_manager.config_manager import ConfigManager
from data_aquisitor.data_aquisitor import DataAquisitor
from ennio_exceptions import VideoAlreadyExist, EnnIOException
from db_manager.db_manager import DbManager
from feature_extractor.video_feature_exractor import VideoFeatureExtractor
from feature_extractor.audio_feature_extractor import AudioFeatureExtractor
from functools import reduce
from ml_core.ml_core import MLCore
import ml_core.mp_utils as mu
from utilities.singleton import Singleton
from utilities.instance_lock import instance_lock, InstanceLock


class EnnIOCore(object, metaclass=Singleton):
    def __init__(self, project_root='.'):
        self._project_root = project_root
        InstanceLock(path=project_root)
        self._config_manager = ConfigManager(path=project_root)
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
        self._video_live_merged = None

    @instance_lock
    def setup(self):
        self._config_manager.read_config()
        self._data_dir = os.path.join(self._project_root, self._config_manager.get_field('data-folder'))
        self._video_download_dir = os.path.join(self._data_dir, "downloads")
        parsed_dir = os.path.join(self._video_download_dir, 'parsed')
        self._evaluation_dir = os.path.join(self._data_dir, 'evaluation')
        eval_parsed_dir = os.path.join(self._evaluation_dir, 'parsed')
        self._eval_video_stream_dir = os.path.join(eval_parsed_dir, 'video')
        self._eval_merged_dir = os.path.join(self._evaluation_dir, 'merged')
        self._video_stream_dir = os.path.join(parsed_dir, 'video')
        self._audio_stream_dir = os.path.join(parsed_dir, 'audio')
        self._url_list_file_location = os.path.join(self._project_root,
                                                    self._config_manager.get_field('urls-list-file'))
        self._model_dir = os.path.join(self._data_dir, 'models')  # added for models by IL 8/2
        self._video_live_dir = os.path.join(self._data_dir, 'live')  # added for models by IL 8/2
        live_parsed_dir = os.path.join(self._video_live_dir, 'parsed')
        self._video_stream_dir_live = os.path.join(live_parsed_dir, 'video')
        self._video_live_merged = os.path.join(self._video_live_dir, 'merged')
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

    @instance_lock
    def on_exit(self):
        self._db_manager.cleanup()

    @instance_lock
    def construct_models(self):
        """
        Method to create and train an ML model. Instantiates MLCore and creates various models.
        If the models are not trained, then they are trained and saved.
        :return:
        """
        return self._construct_models()

    def _construct_models(self):
        """
        Internal method to create and train an ML model. Instantiates MLCore and creates various models.
        If the models are not trained, then they are trained and saved.
        :return:
        """
        vid_df, aud_df, met_df = self._create_dataframes()

        self._ml_core.set_video_dataframe(vid_df)
        self._ml_core.set_audio_dataframe(aud_df)
        self._ml_core.set_metadata_dataframe(met_df)

        self._ml_core.create_models(self._model_dir)

    @staticmethod
    def _audio_video_merge(audio_path, video_path, export_path):
        os.system(f"ffmpeg -y -loglevel quiet -t 60 -i {video_path} -i {audio_path} \
                        -c:v copy -c:a aac -strict experimental {export_path}")

    def _merge_results(self, video_path, results):
        """
        uses audio_video_merge from utilities to produce n+1 clips, where n is the number of models
        :param video_path:
        :param results:
        :return: A dictionary containing a path for each model index
        """
        paths = {}
        for index, audio_path in results.items():
            if index == -1:
                new_name = os.path.basename(video_path) + "_Random.mp4"
            else:
                new_name = os.path.basename(video_path) + "_"\
                           + self._ml_core.get_model_name_from_index(index) + ".mp4"
            export_path = os.path.join(self._eval_merged_dir, new_name)
            self._audio_video_merge(audio_path, video_path, export_path)
            paths[index] = export_path

        return paths

    @instance_lock
    def update_evaluation_vote(self,video_id, winner):
        if winner != "Random":
            for idx, name in enumerate(self._ml_core.available_models):
                if name == winner:
                    winner_idx = idx
                    self._db_manager.update_voted_model(video_id, winner_idx)

    @instance_lock
    def use_models(self, url, start_time_str, mode="prediction"):  # input_file):
        """
        Method to use the existing model in order to predict a
        suitable music score. It assumes that the construct_model above has been called before
        in order to create the models ans store them in a list
        :return: video path, dictionary {model_name: suggested audio path}
        """

        video_path, results = self._use_models(url, start_time_str, mode)
        new_results = {self._ml_core.get_model_name_from_index(index): audio_path
                       for index, audio_path in results.items()}
        return video_path, new_results

    def _use_models(self, url, start_time_str, mode):
        if start_time_str:
            start_time = self._time_string_to_seconds(start_time_str)
        else:
            start_time = 0

        new_vid_ftrs, video_path = self._get_video_features_for_single_file(url=url, start_time=start_time,
                                                                            end_time=start_time + 20, mode=mode)

        # Call predict for all models
        exceptions = []
        results = {}
        self._construct_models()
        predictions = self._ml_core.predict(new_vid_ftrs, video_path)

        for index, clip_id in predictions.items():
            clip = self._db_manager.get_clip_by_id(clip_id)[-1]
            audio = self._db_manager.get_audio_by_id(clip.audio_from_clip)
            if not audio:
                print("Audio does not exist")
                continue

            exceptions.append(clip.audio_from_clip)
            results[index] = audio.audio_path

        if mode == 'evaluation':
            # add a random audio
            rand_audio_id = self._db_manager.get_random_audio(exceptions)
            audio = self._db_manager.get_audio_by_id(rand_audio_id)
            results[-1] = audio.audio_path

        return video_path, results

    @instance_lock
    def download_video_from_url(self, url, start_time_str):
        """
        Method to download a video file from a youtube URL
        :param url: A youtube video URL
        :param start_time_str: Clip start time
        :return: Downloaded file name
        """
        clips = self._db_manager.get_clips_by_url(url)
        if clips:
            print("URL already in DB")
            return
        if start_time_str:
            start_time = self._time_string_to_seconds(start_time_str)
        else:
            start_time = 0
        try:
            path = self._download_video_from_entry(url, start_time,
                                                       start_time + 20)
            return path
        except EnnIOException:
            return

    def _predict_audio_from_models(self, eval_dataframe, url, start_time_str):
        """
        Method to use the best model in order to predict a
        suitable music score. It assumes that the construct_model above has been called before
        in order to create the models ans store them in a list
        :return:
        """
        self._construct_models()

        if start_time_str:
            start_time = self._time_string_to_seconds(start_time_str)
        else:
            start_time = 0

        new_vid_ftrs, video_path = self._get_video_features_for_single_file(url=url, start_time=start_time,
                                                                            end_time=start_time + 20,
                                                                            mode="prediction")

        best_model = mu.model_voter(new_vid_ftrs, eval_dataframe)

        model_prediction_clip_id = self._ml_core.predict_using_model(new_vid_ftrs, new_video_path=video_path,
                                                                     model_idx=int(best_model))

        clip = self._db_manager.get_clip_by_id(model_prediction_clip_id)[-1]
        audio = self._db_manager.get_audio_by_id(clip.audio_from_clip)

        print("Best model: {index}. {audio_path}".format(index=int(best_model),
                                                         audio_path=audio.audio_path))
        return audio.audio_path, video_path

    @instance_lock
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

    def _download_video_from_entry(self, url, start_time, end_time, comment="", mismatch_url="", mismatch_title=""):
        available_cpus = multiprocessing.cpu_count()
        if available_cpus > 1:
            available_cpus -= 1

        self._data_aquisitor.set_download_location(self._video_download_dir)
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

    @instance_lock
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

        print("EVALUATION TABLE")
        print("Number of eval clips in the db: {}".format(len(self._db_manager.dump_evaluation_clips()) - 1))

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

    @instance_lock
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

    @instance_lock
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
        if option == "evaluation_table":
            self._db_manager.clear_user_evaluation_table()
        if option == "models":
            shutil.rmtree(self._model_dir)
            os.makedirs(self._model_dir)

    def _create_evaluation_dataframe(self):
        features = dict()
        for clip in self._db_manager.get_all_evaluation_clips():
            video_features_exist_in_db = clip.video_features != ""

            if video_features_exist_in_db:
                features[clip.clip_id] = np.hstack((np.frombuffer(clip.video_features), clip.voted_model))

        video_df = pd.DataFrame.from_dict(features, orient='index',
                                              columns=self._video_feature_names + ['model_winner'])
        return video_df

    @instance_lock
    def create_dataframe_files(self):
        video_df, audio_df, metadata_df,  = self._create_dataframes()

        options_str = str(self._get_video_extractor_config()).replace(" ", "").replace("'", "").replace(":", "_")
        video_features_file = "video_features_df_{options}.pkl".format(options=options_str)
        video_df.to_pickle(os.path.join(self._data_dir,
                                        video_features_file))

        options_str = str(self._get_audio_extractor_config()).replace(" ", "").replace("'", "").replace(":", "_")
        audio_features_file = "audio_features_df_{options}.pkl".format(options=options_str)
        audio_df.to_pickle(os.path.join(self._data_dir,
                                        audio_features_file))

        metadata_file = "metadata_df.pkl"
        metadata_df.to_pickle(os.path.join(self._data_dir, metadata_file))
        return (os.path.join(self._data_dir, video_features_file),
                os.path.join(self._data_dir, audio_features_file),
                os.path.join(self._data_dir, metadata_file))

    def _create_dataframes(self):
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
        return video_df, audio_df, metadata_df

    def _get_video_features_for_single_file(self, url, start_time, end_time, mode="prediction"):
        """
        Method to get the features for an external video for processing
        :param url: Video url
        :return:
        """
        available_cpus = multiprocessing.cpu_count()
        if available_cpus > 1:
            available_cpus -= 1

        if mode == "prediction":
            self._data_aquisitor.set_download_location(self._video_live_dir)
        else:
            self._data_aquisitor.set_download_location(self._evaluation_dir)

        temp = self._data_aquisitor.download_from_url(url,
                                                      start_time=time.strftime("%M:%S", time.gmtime(start_time)),
                                                      end_time=time.strftime("%M:%S", time.gmtime(end_time)),
                                                      threads=available_cpus)

        if not temp:
            raise EnnIOException("Download from youtube failed")
        metadata = temp[-1]
        video_stream_name = os.path.basename(metadata['filenames'][
                                                 'parsed_video'][-1])

        if mode == "prediction":
            video_file_path = os.path.join(self._video_stream_dir_live,
                                           video_stream_name)
        else:
            video_file_path = os.path.join(self._eval_video_stream_dir,
                                           video_stream_name)

        video_stream_id = self._get_id(video_file_path)

        video_extractor_kw_args = self._get_video_extractor_config()
        video_features, video_feature_names = self._video_feature_extractor.extract_video_features(video_file_path,
                                                                                                   **video_extractor_kw_args)

        size = video_features.shape[0]
        video_features_reshaped = video_features.reshape((1, size))

        if mode == "evaluation":
            if not self._db_manager.evaluation_video_exists(video_stream_id):
                self._db_manager.add_evaluation_clip(clip_id=video_stream_id,
                                                     url=url,
                                                     start_time=start_time,
                                                     end_time=end_time,
                                                     clip_path=video_file_path,
                                                     clip_title=video_stream_name,
                                                     video_features=video_features)
            else:
                raise VideoAlreadyExist("Evaluation already exists for this video")


        video_df = pd.DataFrame(video_features_reshaped, columns=video_feature_names)
        return video_df, video_file_path

    @staticmethod
    def _time_string_to_seconds(time_string):
        return reduce(lambda x, y: x + y, [int(x) * (60 ** i) for i, x in enumerate(time_string.split(":")[::-1])])

    def _clip_exists(self, url, start_time, end_time):
        clips = self._db_manager.get_clips_by_url(url)
        for clip in clips:
            if clip.start_time == start_time and clip.end_time == end_time:
                return True
        return False

    @instance_lock
    def evaluation_mode(self, url, start_time_str):
        """
        :param url: url for evaluation
        :param start_time_str: start time in string format
        :return: paths: a list of 4 combined videos in the form of tuples (video_id, model, path)
        """
        if any(i.isalpha() for i in start_time_str):
            raise EnnIOException("start time must be just digits!")

        # Use model with evaluation parameter
        video_path, results_dict = self._use_models(url, start_time_str, mode='evaluation')
        vid_id = self._db_manager.get_evaluation_clip_by_path(video_path).clip_id
        # Join Video and suggested audio
        results = self._merge_results(video_path, results_dict)

        return vid_id, results

    @instance_lock
    def live_ennio(self, url, start_time_str):
        """
        the live version of ennIO checks with the voter and trains based on best model
        :param url: video url
        :param start_time_str: starting time
        :return: the path of the combined video
        """
        eval_df = self._create_evaluation_dataframe()
        audio_path, video_path = self._predict_audio_from_models(eval_df, url, start_time_str)
        export_path = os.path.join(self._video_live_merged, "Result.mp4")
        self._audio_video_merge(audio_path, video_path, export_path)

        return export_path

