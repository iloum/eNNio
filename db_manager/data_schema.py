import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def clip_header():
    return "clip_id", "url", "clip_title", "clip_description", "clip_path", "video_features", "audio_from_clip"


def audio_header():
    return "audio_id", "audio_features", "audio_path"


class Audio(Base):
    __tablename__ = 'audio'
    audio_id = sql.Column("audio_id", sql.String, primary_key=True)
    audio_features = sql.Column("audio_features", sql.String)
    audio_path = sql.Column("audio_path", sql.String)

    def __init__(self, audio_id="", audio_features="", audio_path=""):
        self.audio_id = audio_id
        self.audio_features = audio_features
        self.audio_path = audio_path.upper()

    def __repr__(self):
        return "{audio_id}, {audio_features},  {path}".format(
            path=self.audio_path,
            audio_features=self.audio_features,
            audio_id=self.audio_id)

    def get_row(self):
        return self.audio_id, self.audio_features, self.audio_path


class Clip(Base):
    __tablename__ = 'clips'
    clip_id = sql.Column(sql.String, primary_key=True)
    clip_description = sql.Column(sql.String)
    clip_title = sql.Column(sql.String)
    url = sql.Column(sql.String)
    clip_path = sql.Column(sql.String)
    video_features = sql.Column("video_features", sql.String)
    audio_from_clip = sql.Column(
        sql.String)  # for training set this column is equal to clip_id. For unknown clips this column will point to the audio of another clip in this table

    def __init__(self, clip_id="", url="",
                 clip_title="", clip_description="", clip_path="", video_features="", audio_from_clip=""):
        self.clip_id = clip_id
        self.clip_description = clip_description
        self.clip_title = clip_title
        self.url = url
        self.clip_path = clip_path
        self.video_features = video_features
        self.audio_from_clip = audio_from_clip

    def __repr__(self):
        return "{id}, {url}, {title}, {descr}, {path}, {feat}, {audio}".format(id=self.clip_id,
                                                                               title=self.clip_title,
                                                                               descr=self.clip_description,
                                                                               url=self.url,
                                                                               path=self.clip_path,
                                                                               feat=self.video_features,
                                                                               audio=self.audio_from_clip)

    def get_row(self):
        return (self.clip_id, self.url, self.clip_title, self.clip_description, self.clip_path,
                self.video_features, self.audio_from_clip)
