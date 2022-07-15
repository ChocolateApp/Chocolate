import os
from videoprops import get_video_properties, get_audio_properties
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

path = config["ChocolateSettings"]["MoviesPath"]
movies = os.listdir(path)
MoviesToConvert = []
newExtension = "mkv"
for movie in movies:
    try:
        movieVideoStats = get_video_properties(f"{path}\\{movie}")
        movieAudioStats = get_audio_properties(f"{path}\\{movie}")
        if os.path.isfile(f"{path}\\{movie}"):
            if movieAudioStats['codec_name'] != "aac":
                MoviesToConvert.append(movie)
    except Exception as e:
        pass
print(f"{len(MoviesToConvert)} films à convertir, environ {len(MoviesToConvert)*0.33} heures de conversions")

for j in MoviesToConvert:
    original_file_title = j.split('.')[0]
    movieAudioStats = get_audio_properties(f"{path}\\{j}")
    command = f'ffmpeg -y -vsync 0 -i "{path}\\{j}" -c:v copy -c:a aac -crf 22 -pix_fmt yuv420p -b:v 5M  "{path}\\Web_{original_file_title}.{newExtension}"'
    os.system(command)
