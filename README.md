# ennIO

ennIO is a modular multi-modal video score recommendation system.

## Installation

### Requirements

#### System
Python3.7 or higher

[FFmpeg](https://www.ffmpeg.org/download.html)

#### Python packages
For Windows:
```shell script
pip install -r requirements_windows.txt
```

For Linux:
```shell script
pip install -r requirements_linux.txt
```

## Usage
### Configuration file
Basic configuration can be done through config.ini file
Available fields:

| Field  	         |   Description	                        |
|--------------------|------------------------------------------|
| [GLOBAL]           |   	                                    |
| data-folder        |  Directory to store all generated data   |
| urls-list-file     |  CSV file containing training data URLs  |
| db-file-name       |  Name of the DB file                     |
| [VIDEO]            |                                          |
| feature-types  	 |  Types of video features to be extracted |
| resize-width  	 |  Video resize width 	                    |
| step  	         |  Seconds between frames	                |
| [AUDIO]  	         |   	                                    |
| mid-term-window  	 |  Window for mid-term averaging 	        |
| mid-term-step  	 |  Step of mid-term window 	            |
| short-term-window  |  Window for short-term averaging 	    |
| short-term-step  	 |  Step of short-term window 	            |

### Command line interface
To run CLI:
```shell script
./ennio.py
```
Available commands:

| Command  	                   |   Description	                                                 |
|------------------------------|-----------------------------------------------------------------|
| download_video_from_url_file |  Download Youtube videos from CSV file configured in config.ini |
| evaluate  	               |  Evaluate models by voting the best match 	                     |
| predict  	                   |  Predict audio 	                                             |
| use_model  	               |  Use all available models to predict the score 	             |
| construct_model              |  Create and train model 	                                     |
| create_dataframes            |  Save extracted features to pickled dataframes 	             |
| download_video_from_url      |  Download Youtube video from url and insert it in training data |
| extract_features  	       |  Extract audio and video features from downloaded file 	     |
| drop                         |  Remove created data. Available options: audio_features,video_features,tables,evaluation_table,models 	 |
| show_status  	               |  Show status information about the ennIO DB 	                 |

### Web interface
To run [Django lightweight development Web server on the local machine](https://docs.djangoproject.com/en/3.0/ref/django-admin/#runserver):
```shell script
./manage.py runserver
```

## License
[GNU General Public License v3.0](https://choosealicense.com/licenses/gpl-3.0/)