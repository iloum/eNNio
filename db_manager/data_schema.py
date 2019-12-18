import sqlalchemy as sql
import datetime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def clip_header():
    return "url", "start_time", "clip_title", "clip_description", "clip_path", "audio_title"


def audio_header():
    return "audio_title", "audio_path"


class Audio(Base):
    __tablename__ = 'audio'
    id = sql.Column(sql.Integer, primary_key=True)
    audio_path = sql.Column(sql.String)
    audio_title = sql.Column(sql.String)

    def __init__(self, audio_title="", audio_path=""):
        self.audio_path = audio_path.upper()
        self.audio_title = audio_title.upper()

    def __repr__(self):
        return "{audio}, {path}".format(
            path=self.audio_path,
            audio=self.audio_title)

    def get_row(self):
        return self.audio_title, self.audio_path


class Clip(Base):
    __tablename__ = 'clips'
    id = sql.Column(sql.Integer, primary_key=True)
    clip_description = sql.Column(sql.String)
    clip_title = sql.Column(sql.String)
    start_time = sql.Column(sql.TIMESTAMP)
    url = sql.Column(sql.String)
    clip_path = sql.Column(sql.String)
    audio_title = sql.Column(sql.String)

    def __init__(self, url="", start_time="", clip_title="", clip_description="",
                 clip_path="", audio_title=""):
        self.clip_description = clip_description.upper()
        self.clip_title = clip_title.upper()
        self.start_time = datetime.datetime.timestamp(datetime.now())
        self.url = url.upper()
        self.clip_path = clip_path.upper()
        self.audio_title = audio_title.upper()

    def __repr__(self):
        return "{url}, {start}, {title}, {descr}, {path}, {audio}".format(title=self.title,
                                                                          descr=self.clip_description,
                                                                          start=self.start_time,
                                                                          url=self.url,
                                                                          path=self.clip_path,
                                                                          audio=self.audio_title)

    def get_row(self):
        return self.url, self.start_time, self.clip_title, self.clip_description, self.clip_path, self.audio_title
