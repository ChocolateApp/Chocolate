from flask import Flask, url_for, request, render_template, redirect, make_response
from flask_cors import CORS
from tmdbv3api import TMDb, Movie, TV
from tmdbv3api.exceptions import TMDbException
from videoprops import get_video_properties, get_audio_properties
from bs4 import BeautifulSoup
from pathlib import Path
import requests, os, subprocess, configparser, socket, datetime, subprocess, socket, platform, GPUtil

app = Flask(__name__)
CORS(app)
tmdb = TMDb()
config = configparser.ConfigParser()
config.read('config.ini')
tmdb.api_key = 'cb862a91645ec50312cf636826e5ca1f'
tmdb.language = config["ChocolateSettings"]["language"]
tmdb.debug = True
movie = Movie()
searchedFilms = []
currentCWD = os.getcwd()
allMovies = []
allMoviesNotSorted = []
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
config.set("ChocolateSettings", "localIP", local_ip)
filmEncode = None
CHUNK_LENGTH = 5
genreList = {
    28: "Action",
    12: "Aventure",
    16: "Animation",
    35: "Comédie",
    80: "Crime",
    99: "Documentaire",
    18: "Drama",
    10751: "Famille",
    14: "Fantastique",
    36: "Histoire",
    27: "Horreur",
    10402: "Musique",
    9648: "Mystère",
    10749: "Romance",
    878: "Science-fiction",
    10770: "TV Movie",
    53: "Thriller",
    10752: "War",
    37: "Western",
}
genresUsed = []


def getMovie(slug):
    for filmData in searchedFilms:
        if filmData["slug"] == slug:
            return filmData


def getMovies():
    movie = Movie()
    try:
        if config["ChocolateSettings"]["MoviesPath"] == "Empty":
            path = str(Path.home() / "Downloads")
        else:
            path = os.path.normpath(config["ChocolateSettings"]["MoviesPath"])
    except KeyError:
        path = str(Path.home() / "Downloads")
    os.chdir(path)
    pythonName ='python' if os.name=='nt' else 'python3'
    print("MovieServer is starting")
    subprocess.Popen([pythonName, f'{currentCWD}\movieServer.py'])


    moviesPathUrl = f"http://localhost:8000"
    pagesMovie = requests.get(moviesPathUrl)
    soupMovies = BeautifulSoup(pagesMovie.content, "html.parser")
    movies = soupMovies.find_all("a")
    filmFileList = []
    for movieFile in movies:
        filmFileList.append(movieFile.text)

    filmFileList = filmFileList
    filmFileList.sort()

    for searchedFilm in filmFileList:   
        if not isinstance(searchedFilm, str):
            continue
        if searchedFilm.endswith("/") == False and searchedFilm.endswith(("mp4", "mp4v", "mov", "avi", "flv", "wmv", "asf", "mpeg","mpg", "mkv", "ts")):
            movieTitle = searchedFilm
            originalMovieTitle = f"{movieTitle.split('.')[0]}.{movieTitle.split('.')[1]}"
            size = len(movieTitle)
            movieTitle = movieTitle[:size - 4]
            try:
                search = movie.search(movieTitle)
            except TMDbException:
                print(TMDbException)
                continue
                
            if not search:
                continue
                
            res = search[0]
            movieTitle = res.title
            movieCoverPath = res.poster_path
            description = res.overview
            note = res.vote_average
            date = res.release_date
            try:
                date = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y")
            except ValueError:
                continue
            genre = res.genre_ids
            video_path = f"{path}\{originalMovieTitle}"
            # convert seconds to hours, minutes and seconds
            length = length_video(video_path)
            length = str(datetime.timedelta(seconds=length))
            length = length.split(":")

            if len(length) == 3:
                hours = length[0]
                minutes = length[1]
                seconds = str(round(float(length[2])))
                if int(seconds) < 10:
                    seconds = f"0{seconds}"
                length = f"{hours}:{minutes}:{seconds}"
            elif len(length) == 2:
                minutes = length[0]
                seconds = str(round(float(length[1])))
                if int(seconds) > 10:
                    seconds = f"0{seconds}"
                length = f"{minutes}:{seconds}"
            elif len(length) == 1:
                seconds = str(round(float(length[0])))
                if int(seconds) > 10:
                    seconds = "0"+seconds
                length = f"00:{seconds}"
            else:
                length = "0"
            
            duration = length

            for genreId in genre:
                if genreList[genreId] not in genresUsed:
                    genresUsed.append(genreList[genreId])
            
            # replace the id with the name of the genre
            movieGenre = []
            for genreId in genre:
                movieGenre.append(genreList[genreId])



            coverFullPath = f"https://image.tmdb.org/t/p/original{movieCoverPath}"

            filmData = {
            "title": movieTitle,
            "cover": coverFullPath,
            "slug": originalMovieTitle,
            "description": description,
            "note": note,
            "date": date,
            "genre": movieGenre,
            "duration": str(duration),
            }



            searchedFilms.append(filmData)
            filmDataToAppend = {
                "title": movieTitle,
                "id": res.id,
                "description": description,
                "note": note,
            }
            allMovies.append(filmDataToAppend)
        elif searchedFilm.endswith("/") == False :
            allMoviesNotSorted.append(searchedFilm)



def length_video(path: str) -> float:
    seconds = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                              "default=noprint_wrappers=1:nokey=1", path], stdout=subprocess.PIPE, text=True)
    return float(seconds.stdout)

def getGpuInfo():
    if platform.system() == "Windows":
        return gpuname()
    elif platform.system() == "Darwin":
        return subprocess.check_output(['/usr/sbin/sysctl', "-n", "machdep.cpu.brand_string"]).strip()
    elif platform.system() == "Linux":
        return "impossible d'accéder au GPU"
    return ""

def gpuname():
    """Returns the model name of the first available GPU"""
    try:
        gpus = GPUtil.getGPUs()
    except:
        print("Unable to detect GPU model. Is your GPU configured? Are you running with nvidia-docker?")
        return "UNKNOWN"
    if len(gpus) == 0:
        raise ValueError("No GPUs detected in the system")
    return gpus[0].name 


@app.route('/')
@app.route('/index')
@app.route('/home')
def home():
    moviesPath = config.get("ChocolateSettings", "MoviesPath")
    filmIsntEmpty = moviesPath != "Empty"
    return render_template('index.html', moviesExist=filmIsntEmpty)

@app.route("/video/<video_name>.m3u8", methods=["GET"])
def create_m3u8(video_name):
    moviesPath = config.get("ChocolateSettings", "MoviesPath")
    video_path = f"{moviesPath}/{video_name}.mkv"
    duration = length_video(video_path)

    file = """
    #EXTM3U
    #EXT-X-VERSION:4
    #EXT-X-TARGETDURATION:5
    """

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""
        #EXTINF:5.0,
        /chunk/{video_name}-{(i // CHUNK_LENGTH) + 1}.ts
        """

    file += """
    #EXT-X-ENDLIST"
    """

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Content-Disposition", "attachment", filename=f"{video_name}.m3u8")

    return response

@app.route("/chunk/<video_name>-<int:idx>.ts", methods=["GET"])
def get_chunk(video_name, idx=0):
    seconds = (idx - 1) * CHUNK_LENGTH
    moviesPath = config.get("ChocolateSettings", "MoviesPath")
    video_path = f"{moviesPath}\{video_name}.mkv"

    time_start = str(datetime.timedelta(seconds=seconds))
    time_end = str(datetime.timedelta(seconds=seconds + CHUNK_LENGTH))

    # check if the server as a nvidia gpu
    serverGPU = getGpuInfo()
    if serverGPU != "UNKNOWN":
        serverGPU = serverGPU.split(" ")[0]
        if serverGPU == "NVIDIA":
            videoCodec = "h264_nvenc"
            PIX = "-pix_fmt"
            PIXcodec = "yuv420p"
            preset = "7"
        else:
            videoCodec = "h264"
            preset = "ultrafast"

    movieVideoStats = get_video_properties(video_path)
    movieAudioStats = get_audio_properties(video_path)
    if movieAudioStats['codec_name'] == "aac" and movieVideoStats['codec_name'] == "h264":
        command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", time_start, "-to", time_end, "-i", video_path,
                "-output_ts_offset", time_start, "-c:v", "copy", "-c:a", "copy", "-preset", "ultrafast", "-ac" ,"2", "-f", "mpegts",
                "pipe:1"]

    elif movieAudioStats['codec_name'] == "aac" and movieVideoStats['codec_name'] != "h264":
        print(f"VideoCodec: {movieVideoStats['codec_name']}")

        if PIX:
            command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", time_start, "-to", time_end, "-i", video_path,
                "-output_ts_offset", time_start, "-c:v", videoCodec, "-c:a", "copy", PIX, PIXcodec,"-preset", "ultrafast", "-ac" ,"2", "-f", "mpegts",
                "pipe:1"]
        else:
            command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", time_start, "-to", time_end, "-i", video_path,
               "-output_ts_offset", time_start, "-c:v", videoCodec, "-c:a", "copy", "-preset", preset, "-ac" ,"2", "-f", "mpegts",
               "pipe:1"]

    elif movieAudioStats['codec_name'] != "aac" and movieVideoStats['codec_name'] == "h264":
        print(f"AudioCodec: {movieAudioStats['codec_name']}")
        command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", time_start, "-to", time_end, "-i", video_path,
               "-output_ts_offset", time_start, "-c:v", "copy", "-c:a", "aac", "-preset", "ultrafast", "-f", "mpegts",
               "pipe:1"]
    else:
        print(f"VideoCodec: {movieVideoStats['codec_name']}\nAudioCodec: {movieAudioStats['codec_name']}")
        if PIX:
            command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", time_start, "-to", time_end, "-i", video_path,
               "-output_ts_offset", time_start, "-c:v", videoCodec, "-c:a", "aac", PIX, PIXcodec, "-preset", preset, "-ac" ,"2", "-f", "mpegts",
               "pipe:1"]
        else:
            command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", time_start, "-to", time_end, "-i", video_path,
               "-output_ts_offset", time_start, "-c:v", videoCodec, "-c:a", "aac", "-preset", preset, "-ac" ,"2", "-f", "mpegts",
               "pipe:1"]

    print(" ".join(command))
    pipe = subprocess.run(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout)
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Content-Disposition", "attachment", filename=f"{video_name}-{idx}.ts")

    return response

@app.route("/films")
def films():
    searchedFilmsUp0 = len(searchedFilms) == 0
    # order by alphabetical order using the id title
    searchedFilms.sort(key=lambda x: x["title"])
    return render_template('films.html', searchedFilms=searchedFilms, conditionIfOne=searchedFilmsUp0)


@app.route("/settings")
def settings():
    global allMoviesNotSorted
    condition = len(allMoviesNotSorted) > 0
    print(allMoviesNotSorted)
    print(condition)
    return render_template("settings.html", notSorted=allMoviesNotSorted, conditionIfOne=condition)

@app.route("/saveSettings/", methods=['POST'])
def saveSettings():
    MoviesPath = request.form['moviesPath']
    language = request.form['language']
    if MoviesPath != "":
        config.set("ChocolateSettings", "moviespath", MoviesPath)
    if language != "":
        config.set("ChocolateSettings", "language", language)
    with open(f'{currentCWD}/config.ini', 'w') as conf:
        config.write(conf)
    return redirect(url_for('settings'))


@app.route("/movie/<slug>")
def movie(slug):
    global filmEncode
    if slug.endswith("ttf") == False:
        moviesPath = config.get("ChocolateSettings", "MoviesPath")
        movieSlug = getMovie(slug)
        movieLink = f"http://{local_ip}:8000/{slug}"
        rewriteSlug = slug.split(".")[0]
        link = f"/video/{rewriteSlug}.m3u8".replace(" ", "%20")
    return render_template("film.html", movieSlug=movieSlug, slug=slug, movieUrl=link)

if __name__ == '__main__':
    getMovies()
    app.run(host="0.0.0.0", port="8500")