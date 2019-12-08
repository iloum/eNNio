import sqlalchemy as sql
import datetime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def clip_header():
    return "clip_description", "clip_title", "start_time", "url", "clip_path"


class Clip(Base):
    __tablename__ = 'clips'
    id = sql.Column(sql.Integer, primary_key=True)
    clip_description = sql.Column(sql.String)
    clip_title = sql.Column(sql.String)
    start_time = sql.Column(sql.TIMESTAMP)
    url = sql.Column(sql.String)
    clip_path = sql.Column(sql.String)

    def __init__(self, clip_title="", clip_description="", start_time="",
                 url="", clip_path=""):
        self.clip_description = clip_description.upper()
        self.clip_title = clip_title.upper()
        self.start_time = datetime.datetime.timestamp(datetime.now())
        self.url = url.upper()
        self.clip_path = clip_path.upper()

    def __repr__(self):
        return "{descr}, {title}, {start}, {url}, {path}".format(title=self.title,
                                                                 descr=self.clip_description,
                                                                 start=self.start_time,
                                                                 url=self.url,
                                                                 path=self.clip_path)

    def get_row(self):
        return self.clip_title, self.clip_description, self.start_time, self.url, self.clip_path