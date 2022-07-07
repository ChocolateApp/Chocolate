from flask import Flask, url_for, request, render_template, redirect, make_response
from flask_cors import CORS
from tmdbv3api import TMDb, Movie, TV
from tmdbv3api.exceptions import TMDbException
from bs4 import BeautifulSoup
from pathlib import Path
import requests, os, subprocess, configparser, socket, datetime, subprocess

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
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
config.set("ChocolateSettings", "localIP", local_ip)
filmEncode = None
CHUNK_LENGTH = 5


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
            originalMovieTitle = f"{movieTitle.split('.')[0]}.{movieTitle.split('.')[1].lower()}"
            size = len(movieTitle)
            movieTitle = movieTitle[:size - 4]
            try:
                search = movie.search(movieTitle)
            except TMDbException:
                continue
                
            if not search:
                continue
                
            res = search[0]
            movieTitle = res.title
            movieCoverPath = res.poster_path
            description = res.overview
            note = res.vote_average
            coverFullPath = f"https://image.tmdb.org/t/p/original{movieCoverPath}"

            filmData = {
            "title": movieTitle,
            "cover": coverFullPath,
            "slug": originalMovieTitle,
            "description": description,
            "note": note
            }

            searchedFilms.append(filmData)
            filmDataToAppend = {
                "title": movieTitle,
                "id": res.id
            }
            allMovies.append(filmDataToAppend)



def length_video(path: str) -> float:
    seconds = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                              "default=noprint_wrappers=1:nokey=1", path], stdout=subprocess.PIPE, text=True)
    return float(seconds.stdout)

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
    print(video_path,'ici')
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
    video_path = f"{moviesPath}/{video_name}.mkv"
    print(video_path,'la')

    time_start = str(datetime.timedelta(seconds=seconds))
    time_end = str(datetime.timedelta(seconds=seconds + CHUNK_LENGTH))

    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", time_start, "-to", time_end, "-i", video_path,
               "-output_ts_offset", time_start, "-c:v", "h264", "-c:a", "aac", "-preset", "ultrafast", "-f", "mpegts",
               "pipe:1"]

    pipe = subprocess.run(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout)
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Content-Disposition", "attachment", filename=f"{video_name}-{idx}.ts")

    return response

@app.route("/films")
def films():
    searchedFilmsUp0 = len(searchedFilms) == 0
    return render_template('films.html', searchedFilms=searchedFilms, conditionIfOne=searchedFilmsUp0)


@app.route("/settings")
def settings():
    return render_template("settings.html")

@app.route("/saveSettings/", methods=['POST'])
def saveSettings():
    MoviesPath = request.form['moviesPath']
    language = request.form['language']
    if MoviesPath != "":
        config.set("ChocolateSettings", "moviespath", MoviesPath)
    if language != "":
        config.set("ChocolateSettings", "language", language)
    with open(f'{currentCWD}\\config.ini', 'w') as conf:
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
        print(link)
    return render_template("film.html", movieSlug=movieSlug, slug=slug, movieUrl=link)

if __name__ == '__main__':
    getMovies()
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port="8500")