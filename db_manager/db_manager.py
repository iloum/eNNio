import sqlalchemy as sql
from sqlalchemy import exc
from sqlalchemy.orm import create_session

from db_manager.data_schema import Base, Clip, clip_header


class DbManager(object):
    """
    CLass that manages all DB operations
    """
    def __init__(self, path="", db_name="library"):
        self._db_name = self.validate_db_name(db_name)
        self.engine = sql.create_engine('sqlite:///{path}{db_name}.db'
                                        .format(path=path, db_name=self.db_name))
        self.session = create_session(bind=self.engine)

    @property
    def db_name(self):
        return self._db_name

    def create_db(self):
        Base.metadata.create_all(self.engine)

    def add_clip(self, **kwargs):
        """

        """
        new_clip = Clip(**kwargs)
        self.session.add(new_clip)
        print(new_clip)
        self.session.flush()

    def save_clip(self):
        self.session.flush()

    def delete_clip(self, row):
        self.session.delete(row)
        self.session.flush()

    def clear_table(self):
        for row in self.get_all_clips():
            self.session.delete(row)
        self.session.flush()

    def get_all_clips(self):
        return self.session.query(Clip).all()

    def cleanup(self):
        self.session.close()

    def search_by_title(self, title):
        return self.session.query(Clip).filter(Clip.clip_title.contains(title.upper())).all()

    def dump_table(self):
        """
        Dumps all entries to a 2-D array
        :return: a tuple containing row entries as tuples
        """
        clips = self.get_all_clips()
        table = list()
        table.append(clip_header())
        table.extend([clip.get_row() for clip in clips])
        return tuple(table)

    def import_table(self, table):
        """
        Creates clip entries from a table and saves them to DB
        :param table: a tuple of tuples containing clip attributes
        """
        attributes_to_index = self.get_indexes_for_book_attributes(table[0])
        clips = self.create_clips_from_table(attributes_to_index, table[1:])
        self.session.add_all(clips)
        self.session.flush()

    @staticmethod
    def get_indexes_for_clip_attributes(header):
        """
        Maps provided table header with the header defined in schema
        :param header: a tuple containing the header
        :return: a dict that maps indexes of header elements to the clip elements
        """
        return dict([(attribute, header.index(attribute)) for attribute in clip_header() if attribute in header])

    def create_clips_from_table(self, attributes_to_index, table):
        """
        Converts all rows of the table to clip objects
        :param attributes_to_index: a dict that maps indexes of header elements to the clip elements
        :param table: a tuple of tuples containing multiple clips
        :return: a list of clip objects
        """
        clips = []
        for row in table:
            try:
                new_clip = Clip(**self.get_book_attributes_from_row(attributes_to_index, row))
                clips.append(new_clip)
            except exc.InvalidInputException:
                continue
        return clips
