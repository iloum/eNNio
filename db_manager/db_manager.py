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

    def video_features_exist_in_db(self, video_id):
        return 'video_features' in self._db[video_id]

    def audio_features_exist_in_db(self, video_id):
        return 'audio_features' in self._db[video_id]

    def save_video_features(self, video_id, video_features):
        self._db[video_id]['video_features'] = video_features

    def save_audio_features(self, video_id, audio_features):
        self._db[video_id]['audio_features'] = audio_features
