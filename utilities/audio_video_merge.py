import os


def audio_video_merge(audio_path, video_path, export_path):
    os.system(f"ffmpeg -y -t 60 -i {video_path} -i {audio_path} \
                    -c:v copy -c:a aac -strict experimental {export_path}")
