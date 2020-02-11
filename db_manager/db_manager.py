import sqlalchemy as sql
from sqlalchemy import exc, exists
from sqlalchemy.orm import create_session
import numpy as np
import os
import random

from db_manager.data_schema import Base, Clip, clip_header, Audio, audio_header, Feature, UserEvaluation, evaluation_header


class DbManager(object):
    """
    CLass that manages all DB operations
    """

    def __init__(self):
        self._db_name = None
        self.engine = None
        self.session = None

    def setup(self, db_file):
        self._db_name = os.path.basename(db_file)
        self.engine = sql.create_engine('sqlite:///{db_file}'
                                        .format(db_file=db_file))
        self.create_db()
        self.session = create_session(bind=self.engine)
        self._auto_create_features()

    @property
    def db_name(self):
        return self._db_name

    def create_db(self):
        Base.metadata.create_all(self.engine)

    def save(self):
        self.session.flush()

    def cleanup(self):
        self.session.close()

    # CLIPS
    def add_clip(self, clip_id="", url="", start_time=0, end_time=0,
                 clip_title="", clip_description="", clip_path="",
                 video_features=None, audio_from_clip="", mismatch_url = "",
                 mismatch_title = ""):
        new_clip = Clip(clip_id=clip_id, url=url,
                        start_time=start_time, end_time=end_time,
                        clip_title=clip_title,
                        clip_description=clip_description,
                        clip_path=clip_path,
                        video_features=video_features.tostring() if
                        video_features else "",
                        audio_from_clip=audio_from_clip,
                        mismatch_url=mismatch_url,
                        mismatch_title=mismatch_title)
        self.session.add(new_clip)
        self.session.flush()

    def url_exists(self, url):
        clips = self.session.query(Clip).filter_by(url=url).all()
        return True if clips else False

    def get_clips_by_url(self, url):
        return self.session.query(Clip).filter_by(url=url).all()

    def video_exists(self, video_id):
        return self.session.query(Clip).filter_by(clip_id=video_id).all()

    def get_clip_by_id(self, id):
        return self.session.query(Clip).filter_by(clip_id=id).all()

    def get_clip_by_audio_id(self, audio_id):
        return self.session.query(Clip).filter_by(audio_from_clip=audio_id).first()

    def clear_clips_table(self):
        for row in self.get_all_clips():
            self.session.delete(row)
        self.session.flush()

    def remove_clip(self, clip):
        """
        Remove single row from clips table
        """
        self.session.delete(clip)
        self.session.flush()

    def clear_video_features(self):
        for row in self.get_all_clips():
            row.video_features = ""
        self.session.flush()

    def get_all_clips(self):
        return self.session.query(Clip).all()

    def dump_clips(self):
        """
        Dumps all entries to a 2-D array
        :return: a tuple containing row entries as tuples
        """
        clips = self.get_all_clips()
        table = list()
        table.append(clip_header())
        table.extend([clip.get_row() for clip in clips])
        return tuple(table)

    # AUDIO
    def add_audio(self, audio_id="", audio_features=None, audio_path=""):
        new_audio = Audio(audio_id=audio_id,
                          audio_features=audio_features.tostring() if
                          audio_features else "",
                          audio_path=audio_path)
        self.session.add(new_audio)
        self.session.flush()

    def audio_exists(self, audio_id):
        return self.session.query(Audio).filter(Audio.audio_id ==
                                                audio_id).all()

    def get_audio_by_id(self, audio_id):
        return self.session.query(Audio).filter(Audio.audio_id ==
                                                audio_id).first()

    def clear_audio_table(self):
        for row in self.get_all_audio():
            self.session.delete(row)
        self.session.flush()

    def remove_audio(self, audio):
        """
        Remove single row from audio table
        """
        self.session.delete(audio)
        self.session.flush()

    def clear_audio_features(self):
        for row in self.get_all_audio():
            row.audio_features = ""
        self.session.flush()

    def get_all_audio(self):
        return self.session.query(Audio).all()

    def dump_audio_table(self):
        """
        Dumps all entries to a 2-D array
        :return: a tuple containing row entries as tuples
        """
        audios = self.get_all_audio()
        table = list()
        table.append(audio_header())
        table.extend([audio.get_row() for audio in audios])
        return tuple(table)

    def get_random_audio(self, exceptions):
        rand = random.randrange(0, self.session.query(Audio).count())
        found = False
        while not found:
            audio_id = self.session.query(Audio)[rand].audio_id
            if audio_id not in exceptions:
                found = True
        return audio_id

    def _update_feature_names(self, feature_type, feature_names):
        instance = self.session.query(Feature).filter(Feature.features_type == feature_type).first()
        instance.feature_names = "|".join(feature_names)
        self.session.flush()

    def update_video_feature_names(self, feature_names):
        self._update_feature_names("video", feature_names)

    def update_audio_feature_names(self, feature_names):
        self._update_feature_names("audio", feature_names)

    def _get_feature_names(self, feature_type):
        instance = self.session.query(Feature).filter(Feature.features_type == feature_type).first()
        return instance.feature_names.split("|")

    def get_video_feature_names(self):
        return self._get_feature_names("video")

    def get_audio_feature_names(self):
        return self._get_feature_names("audio")

    def _auto_create_features(self):
        for features_type in ["video", "audio"]:
            if not self.session.query(Feature).filter(Feature.features_type == features_type).first():
                self.session.add(Feature(features_type=features_type))
                self.session.flush()

    # User Evaluation
    def add_evaluation_clip(self, clip_id="", url="", start_time=0, end_time=0, clip_title="", clip_path="",
                            video_features=None, audio_id="", voted_model=0):
        new_clip = UserEvaluation(clip_id=clip_id, url=url, start_time=start_time, end_time=end_time,
                                  clip_title=clip_title,
                                  clip_path=clip_path,
                                  video_features=video_features.tostring() if
                                  video_features else "",
                                  audio_id=audio_id,
                                  voted_model=voted_model)
        self.session.add(new_clip)
        self.session.flush()

    def evaluation_url_exists(self, url):
        clips = self.session.query(UserEvaluation).filter_by(url=url).all()
        return True if clips else False

    def get_evaluation_clips_by_url(self, url):
        return self.session.query(UserEvaluation).filter_by(url=url).all()

    def get_evaluation_clips_by_path(self, path):
        return self.session.query(UserEvaluation).filter_by(clip_path=path).all()

    def get_evaluation_clip_by_path(self, path):
        return self.session.query(UserEvaluation).filter_by(clip_path=path).first()

    def get_evaluation_clips_by_id(self, id):
        return self.session.query(UserEvaluation).filter_by(clip_id=id).all()

    def evaluation_video_exists(self, video_id):
        return self.session.query(UserEvaluation).filter_by(clip_id=video_id).all()

    def get_evaluation_clip_by_audio_id(self, audio_id):
        return self.session.query(UserEvaluation).filter_by(audio_id=audio_id).first()

    def clear_user_evaluation_table(self):
        for row in self.get_all_evaluation_clips():
            self.session.delete(row)
        self.session.flush()

    def remove_evaluation_clip(self, clip):
        """
        Remove single row from clips table
        """
        self.session.delete(clip)
        self.session.flush()

    def clear_evaluation_video_features_(self):
        for row in self.get_all_evaluation_clips():
            row.video_features = ""
        self.session.flush()

    def get_all_evaluation_clips(self):
        return self.session.query(UserEvaluation).all()

    def dump_evaluation_clips(self):
        """
        Dumps all entries to a 2-D array
        :return: a tuple containing row entries as tuples
        """
        clips = self.get_all_evaluation_clips()
        table = list()
        table.append(evaluation_header())
        table.extend([clip.get_row() for clip in clips])
        return tuple(table)

    def update_voted_model(self, id, voted_model):
        instance = self.session.query(UserEvaluation).filter(UserEvaluation.clip_id == id).first()
        instance.voted_model = voted_model
        self.session.flush()
