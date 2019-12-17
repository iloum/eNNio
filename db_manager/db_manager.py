import pickle
import os

class DbManager:
    def __init__(self):
        self._db_file = None
        self._urls = list()
        self._db = dict()

    def setup(self, db_file):
        self._db_file = db_file
        if os.path.exists(self._db_file):
            with open(self._db_file, "rb") as f:
                self._db, self._urls = pickle.load(f)

    def is_url_in_db(self, url):
        return url in self._urls

    def is_video_id_in_db(self, video_id):
        return video_id in self._db.keys()

    def save_video_data(self, video_id, filename, file_path, url):
        self._urls.append(url)
        self._db[video_id] = {'filename': filename,
                              'file_path': file_path,
                              'url': url}

    def close_db(self):
        with open(self._db_file, "wb") as f:
            pickle.dump((self._db, self._urls), f)