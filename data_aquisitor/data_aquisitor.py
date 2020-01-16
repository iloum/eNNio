from data_aquisitor.Bifrost import get_videos
import time
import tempfile
from collections import namedtuple


class DataAquisitor:
    def __init__(self):
        self._download_location = None

    def set_download_location(self, path):
        self._download_location = path

    def set_metadata(self,metadata):
        self._metadata = metadata

    def download_from_url(self, url, start_time=None, end_time=None,threads=5):
        """
        Method to download youtube videos from a URL list
        :param url: Youtube video URL
        :param start_time: Starting time of the scene
        :param end_time: Ending time of the scene
        :return: filename
        """
        dummy_csv_headers="link|timestamps|res|fps|abr"
        if not start_time and not end_time:
            dummy_csv_body="%s|[[00:00,59:59]]|144|30|50"%(url)
        elif start_time and end_time:
            dummy_csv_body="%s|[[%s,%s]]|144|30|50"%(url,start_time,end_time)
        else:
            raise Exception("you have to either specify both or none of the timestamps for url ",url)
        

        args=namedtuple("args","filename outputfolder threads")

        temp_filename="url_temp_"+str(round(time.time()))+".csv"
        with tempfile.NamedTemporaryFile(mode="wt") as f:
            f.write(dummy_csv_headers+"\n")
            f.write(dummy_csv_body)
            f.seek(0)
            videoargs=args(f.name,self._download_location,threads)
            persisted_metadata,onego_metadata=get_videos.main(videoargs)

        self.set_metadata(persisted_metadata)
        return onego_metadata


    def download_from_url_2(self, url, timeslices=[[]]):
        """
        Method to download youtube videos from a URL list
        :param url: Youtube video URL
        :timeslices: 

        scene 1       ....       scene 10   ...
            |                       |
            v                       V
        [[start1, end1],...,[start10,end10]...]  \ 
        
            one scene of ten(or more) timestamps
                            |
                            v
        [[ [start1,end1],...,[start10,end10] ]]. 
        
        above can be combined
        
        :return: filename
        """
        pass

    def download_from_csv(self,csv_path,threads=5):
        """
        Method to download data from csv 
        :csv_path: path to csv
        ------
        format
        -------
        link|timestamps|res|fps|abr
        https://www.youtube.com/watch?v=OQfusjHRO4s|[[00:39,01:24]]|144|30|50
        """
        args=namedtuple("args","filename outputfolder threads")
        videoargs=args(csv_path,self._download_location,threads)
        persisted_metadata,onego_metadata=get_videos.main(videoargs)

        self.set_metadata(persisted_metadata)
        return onego_metadata

    def get_metadata(self):
        """
        returns metadata stored in data aquisitor.
        :return: Dictionary of metadata
        """
        return self._metadata
        
if __name__ == '__main__':
    da=DataAquisitor()
    da.set_download_location("./outputs")
    
    print("test1")
    meta=da.download_from_url("https://www.youtube.com/watch?v=TYPp-DkuLwg")
    print(meta)
    print("-------")
    print(da.get_metadata())

    print("test2")
    meta=da.download_from_url("https://www.youtube.com/watch?v=TYPp-DkuLwg","00:05","01:00")
    print(meta)
    print("-------")
    print(da.get_metadata())

    print("test3")
    meta=da.download_from_csv("./sample_url_list.csv")
    print(meta)
    print("-------")
    print(da.get_metadata())
