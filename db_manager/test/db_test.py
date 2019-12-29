import unittest
from db_manager.db_manager import DbManager
import numpy as np
from os import path


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.manager = DbManager()
        self.manager.create_db()
        # self.assertEqual(True, False)

    def tearDown(self):
        self.manager.clear_clips_table()
        self.manager.cleanup()

    def add_a_clip(self):
        self.manager.add_clip(clip_id="ena", url="youtube1", clip_title="prwto clip",
                              clip_description="oreo video", clip_path="C:/videos",
                              video_features=np.ones(354))

    def test_create_db(self):
        self.assertTrue(path.exists("eNNio_DB.db"))

    def test_add_clip(self):
        self.manager.add_clip(clip_id="dyo", url="youtube2", clip_title="2o clip",
                              clip_description="poly oreo video", clip_path="C:/videos",
                              video_features=np.ones(354))
        rows = self.manager.get_all_clips()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[-1].clip_title, "2o clip")

    def test_get_by_id(self):
        self.manager.add_clip(clip_id="dyo", url="youtube2", clip_title="2o clip",
                              clip_description="poly oreo video", clip_path="C:/videos",
                              video_features=np.ones(354))
        p = self.manager.get_clip_by_id(clip_id="dyo")
        self.assertEqual(p["clip_id"],"dyo")

    def test_get_video_features(self):
        self.manager.add_clip(clip_id="dyo", url="youtube2", clip_title="2o clip",
                              clip_description="poly oreo video", clip_path="C:/videos",
                              video_features=np.ones(354))
        p = self.manager.get_clip_by_id("dyo")
        self.assertIs(type(p["video_features"]), np.ndarray)



if __name__ == '__main__':
    unittest.main()
