import sqlalchemy as sql
from sqlalchemy import exc, exists
from sqlalchemy.orm import create_session
import numpy as np

from db_manager.data_schema import Base, Clip, clip_header, Audio, audio_header


class DbManager(object):
    """
    CLass that manages all DB operations
    """

    def __init__(self, path="", db_name="eNNio_DB"):
        self._db_name = db_name
        self.engine = sql.create_engine('sqlite:///{path}{db_name}.db'
                                        .format(path=path, db_name=self.db_name))
        self.session = create_session(bind=self.engine)

    @property
    def db_name(self):
        return self._db_name

    def create_db(self):
        Base.metadata.create_all(self.engine)

    def save_clip(self):
        self.session.flush()

    def cleanup(self):
        self.session.close()

    #CLIPS
    def add_clip(self, clip_id="", url="",
                 clip_title="", clip_description="", clip_path="", video_features=np.zeros(354), audio_from_clip=""):
        new_clip = Clip(clip_id=clip_id, url=url, clip_title=clip_title,
                        clip_description=clip_description,
                        clip_path=clip_path, video_features=video_features.tostring(),
                        audio_from_clip=audio_from_clip)
        self.session.add(new_clip)
        self.session.flush()

    def url_exists(self, url):
        return self.session.query(exists().where(Clip.url == url))

    def video_exists(self, video_id):
        return self.session.query(exists().where(Clip.clip_id == video_id))

    def get_clip_by_id(self, clip_id=""):
        q = self.session.query(Clip).filter(Clip.clip_id == clip_id).all()
        p = dict.fromkeys(clip_header(), "0")
        for record in q:
            for col in clip_header():
                if col == "video_features":
                    p[col] = np.frombuffer(record.__dict__[col])
                else:
                    p[col] = record.__dict__[col]
        return p

    def clear_clips_table(self):
        for row in self.get_all_clips():
            self.session.delete(row)
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

    @staticmethod
    def get_indexes_for_clip_attributes(header):
        """
        Maps provided table header with the header defined in schema
        :param header: a tuple containing the header
        :return: a dict that maps indexes of header elements to the clip elements
        """
        return dict([(attribute, header.index(attribute)) for attribute in clip_header() if attribute in header])

    @staticmethod
    def get_clip_attributes_from_row(attributes_to_index, row):
        clip_args = dict()
        for key, index in attributes_to_index.items():
            value = row[index]
            if value:
                clip_args[key] = row[index]
        if not clip_args["author"] or not clip_args["title"]:
            raise exc.InvalidInputException
        return clip_args

    #AUDIO

    def add_audio(self, audio_id="", audio_features=np.zeros(66), audio_path=""):
        new_audio = Audio(audio_id=audio_id, audio_features=audio_features.tostring(), audio_path=audio_path)
        self.session.add(new_audio)
        self.session.flush()

    def audio_exists(self, audio_id):
        return self.session.query(exists().where(Audio.clip_id == audio_id))

    def get_audio_by_id(self, audio_id):
        q = self.session.query(Audio).filter(Audio.audio_id == audio_id)
        p = dict.fromkeys(audio_header(), 0)
        for col in clip_header():
            if col == "audio_features":
                p[col] = np.fromstring(q[col])
            else:
                p[col] = q[col]
        return p

    def clear_audio_table(self):
        for row in self.get_all_audio():
            self.session.delete(row)
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
