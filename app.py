from sqlite3 import IntegrityError
from flask import Flask, url_for, request, render_template, redirect, make_response, send_file, g
from markupsafe import Markup
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from tmdbv3api import TMDb, Movie, TV, Episode, Person
from tmdbv3api.exceptions import TMDbException
from videoprops import get_video_properties
from Levenshtein import distance as lev
from ask_lib import AskResult, ask
from deep_translator import GoogleTranslator
from time import mktime
from PIL import Image
from pypresence import Presence
import requests, os, subprocess, configparser, socket, datetime, subprocess, socket, platform, GPUtil, json, time, sqlalchemy, warnings, re, zipfile, ast, git

start_time = mktime(time.localtime())

with warnings.catch_warnings():
   warnings.simplefilter("ignore", category = sqlalchemy.exc.SAWarning)

app = Flask(__name__)
CORS(app)

dirPath = os.getcwd()
dirPath = os.path.dirname(__file__).replace("\\", "/")
app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///{dirPath}/database.db'
app.config['MAX_CONTENT_LENGTH'] = 4096 * 4096
app.config['UPLOAD_FOLDER'] = f"{dirPath}/static/img/"
app.config["SECRET_KEY"] = "ChocolateDBPassword"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
loginManager = LoginManager()
loginManager.init_app(app)
loginManager.login_view = 'login'
langs_dict = GoogleTranslator().get_supported_languages(as_dict=True)

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    profilePicture = db.Column(db.String(255))
    accountType = db.Column(db.String(255))

    def __init__(self, name, password, profilePicture, accountType):
        self.name = name
        self.password = generate_password_hash(password)
        self.profilePicture = profilePicture
        self.accountType = accountType

    def __repr__(self) -> str:
        return f'<Name {self.name}>'

    def verify_password(self, pwd):
        return check_password_hash(self.password, pwd)

class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), primary_key=True)
    realTitle = db.Column(db.String(255), primary_key=True)
    cover = db.Column(db.String(255))
    banner = db.Column(db.String(255))
    slug = db.Column(db.String(255))
    description = db.Column(db.String(2550))
    note = db.Column(db.String(255))
    date = db.Column(db.String(255))
    genre = db.Column(db.String(255))
    duration = db.Column(db.String(255))
    cast = db.Column(db.String(255))
    bandeAnnonceUrl = db.Column(db.String(255))
    adult = db.Column(db.String(255))
    libraryName=db.Column(db.String(255))
    alternativesNames = db.Column(db.Text)
    vues = db.Column(db.Text, default=str({}))

    def __init__(self, id, title, realTitle, cover, banner, slug, description, note, date, genre, duration, cast, bandeAnnonceUrl, adult, libraryName, alternativesNames, vues):
        self.id = id
        self.title = title
        self.realTitle = realTitle
        self.cover = cover
        self.banner = banner
        self.slug = slug
        self.description = description
        self.note = note
        self.date = date
        self.genre = genre
        self.duration = duration
        self.cast = cast
        self.bandeAnnonceUrl = bandeAnnonceUrl
        self.adult = adult
        self.libraryName = libraryName
        self.alternativesNames = alternativesNames
        self.vues = vues
    
    def __repr__(self) -> str:
        return f"<Movies {self.title}>"

class Series(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), primary_key=True)
    originalName = db.Column(db.String(255), primary_key=True)
    genre = db.Column(db.String(255))
    duration = db.Column(db.String(255))
    description = db.Column(db.String(2550))
    cast = db.Column(db.String(255))
    bandeAnnonceUrl = db.Column(db.String(255))
    serieCoverPath = db.Column(db.String(255))
    banniere = db.Column(db.String(255))
    note = db.Column(db.String(255))
    date = db.Column(db.String(255))
    serieModifiedTime = db.Column(db.Float)
    libraryName=db.Column(db.String(255))
    adult = db.Column(db.String(255))

    def __init__(self, id, name, originalName, genre, duration, description, cast, bandeAnnonceUrl, serieCoverPath, banniere, note, date, serieModifiedTime, adult, libraryName):
        self.id = id
        self.name = name
        self.originalName = originalName
        self.genre = genre
        self.duration = duration
        self.description = description
        self.cast = cast
        self.bandeAnnonceUrl = bandeAnnonceUrl
        self.serieCoverPath = serieCoverPath
        self.banniere = banniere
        self.note = note
        self.date = date
        self.serieModifiedTime = serieModifiedTime
        self.libraryName = libraryName
        self.adult = adult
    
    def __repr__(self) -> str:
        return f"<Series {self.name}>"


class Seasons(db.Model):
    
    serie = db.Column(db.Integer, nullable=False)
    seasonId = db.Column(db.Integer, primary_key=True)
    seasonNumber = db.Column(db.Integer, primary_key=True)
    release = db.Column(db.String(255))
    episodesNumber = db.Column(db.String(255))
    seasonName = db.Column(db.String(255))
    seasonDescription = db.Column(db.Text)
    seasonCoverPath = db.Column(db.String(255))
    modifiedDate = db.Column(db.Float)

    def __init__(self, serie, release, episodesNumber, seasonNumber, seasonId, seasonName, seasonDescription, seasonCoverPath, modifiedDate):
        self.serie = serie
        self.release = release
        self.episodesNumber = episodesNumber
        self.seasonNumber = seasonNumber
        self.seasonId = seasonId
        self.seasonName = seasonName
        self.seasonDescription = seasonDescription
        self.seasonCoverPath = seasonCoverPath
        self.modifiedDate = modifiedDate

    def __repr__(self) -> str:
        return f"<Seasons {self.serie} {self.seasonNumber}>"

class Episodes(db.Model):
    seasonId = db.Column(db.Integer, nullable=False)
    episodeId = db.Column(db.Integer, primary_key=True)
    episodeName = db.Column(db.String(255), primary_key=True)
    episodeNumber = db.Column(db.Integer, primary_key=True)
    episodeDescription = db.Column(db.Text)
    episodeCoverPath = db.Column(db.String(255))
    releaseDate = db.Column(db.String(255))
    slug = db.Column(db.String(255))
    introStart = db.Column(db.Float)
    introEnd = db.Column(db.Float)

    def __init__(self, episodeId, episodeName, seasonId, episodeNumber, episodeDescription, episodeCoverPath, releaseDate, slug, introStart, introEnd):
        self.episodeId = episodeId
        self.seasonId = seasonId
        self.episodeName = episodeName
        self.episodeNumber = episodeNumber
        self.episodeDescription = episodeDescription
        self.episodeCoverPath = episodeCoverPath
        self.releaseDate = releaseDate
        self.slug = slug
        self.introStart = introStart
        self.introEnd = introEnd

    def __repr__(self) -> str:
        return f"<Episodes {self.seasonId} {self.episodeNumber}>"

class Games(db.Model):
    console = db.Column(db.String(255), nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), primary_key=True)
    realTitle = db.Column(db.String(255), primary_key=True)
    cover = db.Column(db.String(255))
    description = db.Column(db.String(2550))
    note = db.Column(db.String(255))
    date = db.Column(db.String(255))
    genre = db.Column(db.String(255))
    slug = db.Column(db.String(255))
    libraryName=db.Column(db.String(255))

    def __init__(self, console, id, title, realTitle, cover, description, note, date, genre, slug, libraryName):
        self.console = console
        self.id = id
        self.title = title
        self.realTitle = realTitle
        self.cover = cover
        self.description = description
        self.note = note
        self.date = date
        self.genre = genre
        self.slug = slug
        self.libraryName = libraryName
    
    def __repr__(self) -> str:
        return f"<Games {self.title}>"

class Language(db.Model):
    language = db.Column(db.String(255), primary_key=True)
    
    def __init__(self, language):
        self.language = language
    
    def __repr__(self) -> str:
        return f"<Language {self.language}>"

class Actors(db.Model):
    name = db.Column(db.String(255), primary_key=True)
    actorId = db.Column(db.Integer, primary_key=True)
    actorImage = db.Column(db.Text)
    actorDescription = db.Column(db.String(2550))
    actorBirthDate = db.Column(db.String(255))
    actorBirthPlace = db.Column(db.String(255))
    actorPrograms = db.Column(db.Text)

    def __init__(self, name, actorId, actorImage, actorDescription, actorBirthDate, actorBirthPlace, actorPrograms):
        self.name = name
        self.actorId = actorId
        self.actorImage = actorImage
        self.actorDescription = actorDescription
        self.actorBirthDate = actorBirthDate
        self.actorBirthPlace = actorBirthPlace
        self.actorPrograms = actorPrograms
    
    def __repr__(self) -> str:
        return f"<Actors {self.name}>"

class Libraries(db.Model):
    libName = db.Column(db.String(255), primary_key=True)
    libImage = db.Column(db.String(255))
    libType = db.Column(db.String(255))
    libFolder = db.Column(db.Text)
    availableFor = db.Column(db.Text)

    def __init__(self, libName, libImage, libType, libFolder, availableFor):
        self.libName = libName
        self.libImage = libImage
        self.libType = libType
        self.libFolder = libFolder
        self.availableFor = availableFor
    
    def __repr__(self) -> str:
        return f"<Libraries {self.libName}>"


with app.app_context():
  db.create_all()
  db.init_app(app)

@loginManager.user_loader
def load_user(id):
    return Users.query.get(int(id))


config = configparser.ConfigParser()


dir = os.path.dirname(__file__)
config.read(os.path.join(dir, 'config.ini'))
if config["ChocolateSettings"]["language"] == "Empty":
    config["ChocolateSettings"]["language"] = "EN"

chocolateVersion = config["ChocolateSettings"]["version"]
repo = git.Repo(search_parent_directories=True)
lastCommitHash = repo.head.object.hexsha[:7]
with app.app_context():
    libraries = Libraries.query.filter_by(libType="games").all() is not None
    if libraries:
        clientID = config.get("APIKeys", "IGDBID")
        clientSecret = config.get("APIKeys", "IGDBSECRET")
        if clientID == "Empty" or clientSecret == "Empty":
            print("Follow this tutorial to get your IGDB API Keys: https://api-docs.igdb.com/#account-creation")
            clientID = input("Please enter your IGDB Client ID: ")
            clientSecret = input("Please enter your IGDB Client Secret: ")
            config.set("APIKeys", "IGDBID", clientID)
            config.set("APIKeys", "IGDBSECRET", clientSecret)
            with open(os.path.join(dir, 'config.ini'), "w") as conf:
                config.write(conf)

tmdb = TMDb()
apiKeyTMDB = config["APIKeys"]["TMDB"]
if apiKeyTMDB == "Empty":
    print("Follow this tutorial to get your TMDB API Key : https://developers.themoviedb.org/3/getting-started/introduction")
    apiKey = input("Please enter your TMDB API Key: ")
    config["APIKeys"]["TMDB"] = apiKey
tmdb.api_key = config["APIKeys"]["TMDB"]

def searchGame(game, console):
    url = f"https://www.igdb.com/search_autocomplete_all?q={game.replace(' ', '%20')}"
    return IGDBRequest(url,console)

def IGDBRequest(url, console):
    customHeaders = {
        'User-Agent': 'Mozilla/5.0 (X11; UwUntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0',
        'Accept': '*/*',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': url,
        'DNT': '1',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Referer': url,
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
    }
    response = requests.request("GET", url, headers=customHeaders)
    
    if response.status_code == 403:
        return None
    elif response.json() != {}:
        grantType = "client_credentials"
        getAccessToken = f"https://id.twitch.tv/oauth2/token?client_id={clientID}&client_secret={clientSecret}&grant_type={grantType}"
        token = requests.request("POST", getAccessToken)
        token = token.json()
        token = token["access_token"]

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "Client-ID": clientID
        }

        games = response.json()["game_suggest"]
        for i in games:
            game=i
            gameId = game["id"]
            url = f"https://api.igdb.com/v4/games"
            body = f"fields name, cover.*, summary, total_rating, first_release_date, genres.*, platforms.*; where id = {gameId};"
            response = requests.request("POST", url, headers=headers, data=body)
            if len(response.json())==0:
                break
            game = response.json()[0]
            if "platforms" in game:
                gamePlatforms = game["platforms"]
                try:
                    platforms = [i["abbreviation"] for i in gamePlatforms]

                    realConsoleName = {
                        "GB": "Game Boy",
                        "GBA": "Game Boy Advance",
                        "GBC": "Game Boy Color",
                        "N64": "Nintendo 64",
                        "NES": "Nintendo Entertainment System",
                        "NDS": "Nintendo DS",
                        "SNES": "Super Nintendo Entertainment System",
                        "Sega Master System": "Sega Master System",
                        "Sega Mega Drive": "Sega Mega Drive",
                        "PS1": "PS1"
                    }

                    if realConsoleName[console] not in platforms and console not in platforms:
                        continue
                    if "total_rating" not in game:
                        game["total_rating"] = "Unknown"
                    if "genres" not in game:
                        game["genres"] = [{"name": "Unknown"}]
                    if "summary" not in game:
                        game["summary"] = "Unknown"
                    if "first_release_date" not in game:
                        game["first_release_date"] = "Unknown"
                    if "cover" not in game:
                        game["cover"] = {"url": "//images.igdb.com/igdb/image/upload/t_cover_big/nocover.png"}

                    game["summary"] = translate(game["summary"])
                    game["genres"][0]["name"] = translate(game["genres"][0]["name"])


                    genres = []
                    for genre in game["genres"]:
                        genres.append(genre["name"])
                    genres = ", ".join(genres)

                    gameData = {
                        "title": game["name"],
                        "cover": game["cover"]["url"].replace("//", "https://"),
                        "description": game["summary"],
                        "note": game["total_rating"],
                        "date": game["first_release_date"],
                        "genre": genres,
                        "id": game["id"]
                    }
                    return gameData
                except:
                    continue
        return None

def translate(string):
    language = config["ChocolateSettings"]["language"]
    if language == "EN":
        return string
    translated = GoogleTranslator(source='english', target=language.lower()).translate(string)
    return translated



tmdb.language = config["ChocolateSettings"]["language"].lower()
tmdb.debug = True

movie = Movie()
show = TV()

errorMessage = True
client_id = "771837466020937728"

enabledRPC = config["ChocolateSettings"]["discordrpc"]
if enabledRPC == "true":
    try:
        RPC = Presence(client_id)
        RPC.connect()
    except Exception as e:
        enabledRPC == "false"
        config.set("ChocolateSettings", "discordrpc", "false")
        with open(os.path.join(dir, 'config.ini'), "w") as conf:
            config.write(conf)
searchedFilms = []
allMoviesNotSorted = []
searchedSeries = []
simpleDataSeries = {}
allSeriesNotSorted = []
allSeriesDict = {}
allSeriesDictTemp = {}

hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
config.set("ChocolateSettings", "localIP", local_ip)
serverPort = config["ChocolateSettings"]["port"]
configLanguage = config["ChocolateSettings"]["language"]
with app.app_context():
    languageDB = db.session.query(Language).first()
    exists = db.session.query(Language).first() is not None
    if not exists:
        newLanguage = Language(language="EN")
        db.session.add(newLanguage)
        db.session.commit()
    languageDB = db.session.query(Language).first()
    if languageDB.language != configLanguage:
        db.session.query(Movies).delete()
        db.session.query(Series).delete()
        db.session.query(Seasons).delete()
        db.session.query(Episodes).delete()
        languageDB.language = configLanguage
        db.session.commit()

CHUNK_LENGTH = 5
genreList = {
    12: "Aventure",
    14: "Fantastique",
    16: "Animation",
    18: "Drama",
    27: "Horreur",
    28: "Action",
    35: "Comédie",
    36: "Histoire",
    37: "Western",
    53: "Thriller",
    80: "Crime",
    99: "Documentaire",
    878: "Science-fiction",
    9648: "Mystère",
    10402: "Musique",
    10749: "Romance",
    10751: "Famille",
    10752: "War",
    10759: "Action & Adventure",
    10762: "Kids",
    10763: "News",
    10764: "Reality",
    10765: "Sci-Fi & Fantasy",
    10766: "Soap",
    10767: "Talk",
    10768: "War & Politics",
    10769: "Western",
    10770: "TV Movie",
}

genresUsed = []
moviesGenre = []
movieExtension = ""
websitesTrailers = {
    "YouTube": "https://www.youtube.com/embed/",
    "Dailymotion": "https://www.dailymotion.com/video/",
    "Vimeo": "https://vimeo.com/",
}

def getMovies(libraryName):
    movie = Movie()
    path = Libraries.query.filter_by(libName=libraryName).first().libFolder
    try:
        os.chdir(path)
    except OSError as e:
        print("No movies found")
        return
    filmFileList = []
    movies = os.listdir(path)
    for movieFile in movies:
        if os.path.isfile(f"{path}/{movieFile}"):
            filmFileList.append(movieFile)

    filmFileList.sort()

    for searchedFilm in filmFileList:
        if not isinstance(searchedFilm, str):
            continue
        if not searchedFilm.endswith("/") and searchedFilm.endswith(("mp4", "mp4v", "mov", "avi", "flv", "wmv", "asf", "mpeg", "mpg", "mkv", "ts")):
            movieTitle = searchedFilm
            originalMovieTitle = movieTitle
            size = len(movieTitle)
            movieTitle, extension = os.path.splitext(movieTitle)
            index = filmFileList.index(searchedFilm) + 1
            percentage = index * 100 / len(filmFileList)

            loadingFirstPart = ("•" * int(percentage * 0.2))[:-1]
            loadingFirstPart = f"{loadingFirstPart}➤"
            loadingSecondPart = "•" * (20 - int(percentage * 0.2))
            loading = f"{str(int(percentage)).rjust(3)}% | [\33[32m{loadingFirstPart} \33[31m{loadingSecondPart}\33[0m] | {movieTitle} | {index}/{len(filmFileList)}                                                      "
            print("\033[?25l", end="")
            print(loading, end="\r", flush=True)
            
            with app.app_context():
                exists = db.session.query(Movies).filter_by(title=movieTitle).first() is not None
                if not exists:
                    movie = Movie()
                    try:
                        search = movie.search(movieTitle, adult=True)
                    except TMDbException:
                        print(TMDbException)
                        allMoviesNotSorted.append(search)
                        continue

                    if not search:
                        print(f"Movie {movieTitle} not found")
                        allMoviesNotSorted.append(originalMovieTitle)
                        continue
                    if config["ChocolateSettings"]["askwhichmovie"] == "false" or len(search)==1:
                        bestMatch = search[0]
                        for i in range(len(search)):
                            if (lev(movieTitle, search[i].title) < lev(movieTitle, bestMatch.title)
                                and bestMatch.title not in filmFileList):
                                bestMatch = search[i]
                            elif (lev(movieTitle, search[i].title) == lev(movieTitle, bestMatch.title)
                                and bestMatch.title not in filmFileList):
                                bestMatch = bestMatch
                            if (lev(movieTitle, bestMatch.title) == 0
                                and bestMatch.title not in filmFileList):
                                break
                    else:
                        print(f"I found {len(search)} movies for {movieTitle}                                       ")
                        for serieSearched in search:
                            indexOfTheSerie = search.index(serieSearched)
                            try:
                                print(f"{serieSearched.title} id:{indexOfTheSerie} date:{serieSearched.release_date}")
                            except:
                                print(f"{serieSearched.title} id:{indexOfTheSerie} date:Unknown")
                        valueSelected = int(input("Which movie is it (id):"))
                        if valueSelected < len(search):
                            bestMatch = search[valueSelected]

                    res = bestMatch
                    try:
                        name = res.title
                    except AttributeError as e:
                        name = res.original_title
                    movieId = res.id
                    details = movie.details(movieId)

                    movieCoverPath = f"https://image.tmdb.org/t/p/original{res.poster_path}"
                    banniere = f"https://image.tmdb.org/t/p/original{res.backdrop_path}"
                    rewritedName = movieTitle.replace(" ", "_")
                    if not os.path.exists(f"{dirPath}/static/img/mediaImages/{rewritedName}_Cover.webp"):
                        with open(f"{dirPath}/static/img/mediaImages/{rewritedName}_Cover.png", "wb") as f:
                            f.write(requests.get(movieCoverPath).content)
                        try:
                            img = Image.open(f"{dirPath}/static/img/mediaImages/{rewritedName}_Cover.png")
                            img.save(f"{dirPath}/static/img/mediaImages/{rewritedName}_Cover.webp", "webp")
                            os.remove(f"{dirPath}/static/img/mediaImages/{rewritedName}_Cover.png")
                            movieCoverPath = f"/static/img/mediaImages/{rewritedName}_Cover.webp"
                        except:
                            os.rename(f"{dirPath}/static/img/mediaImages/{rewritedName}_Cover.png", f"{dirPath}/static/img/mediaImages/{rewritedName}_Cover.webp")
                            movieCoverPath = "/static/img/broken.webp"
                    else:
                        movieCoverPath = f"/static/img/mediaImages/{rewritedName}_Cover.webp"

                    if not os.path.exists(f"{dirPath}/static/img/mediaImages/{rewritedName}_Banner.webp"):
                        with open(f"{dirPath}/static/img/mediaImages/{rewritedName}_Banner.png", "wb") as f:
                            f.write(requests.get(banniere).content)
                        if res.backdrop_path == None:
                            banniere = f"https://image.tmdb.org/t/p/original{details.backdrop_path}"
                            if banniere != "https://image.tmdb.org/t/p/originalNone":
                                with open(f"{dirPath}/static/img/mediaImages/{rewritedName}_Banner.png", "wb") as f:
                                    f.write(requests.get(banniere).content)
                            else:
                                banniere = "/static/img/broken.webp"
                        try:
                            img = Image.open(f"{dirPath}/static/img/mediaImages/{rewritedName}_Banner.png")
                            img.save(f"{dirPath}/static/img/mediaImages/{rewritedName}_Banner.webp", "webp")
                            os.remove(f"{dirPath}/static/img/mediaImages/{rewritedName}_Banner.png")
                            banniere = f"/static/img/mediaImages/{rewritedName}_Banner.webp"
                        except:
                            os.rename(f"{dirPath}/static/img/mediaImages/{rewritedName}_Banner.png", f"{dirPath}/static/img/mediaImages/{rewritedName}_Banner.webp")
                            banniere = "/static/img/brokenBanner.webp"
                    else:
                        banniere = f"/static/img/mediaImages/{rewritedName}_Banner.webp"

                    description = res.overview
                    note = res.vote_average
                    try:
                        date = res.release_date
                    except AttributeError as e:
                        date = "Unknown"

                    casts = details.casts.cast[:5]
                    theCast = []
                    for cast in casts:
                        characterName = cast.character
                        actorName = (
                            cast.name.replace(" ", "_")
                            .replace("/", "")
                            .replace("\"", "")
                        )
                        actorImage = f"https://www.themoviedb.org/t/p/w600_and_h900_bestv2{cast.profile_path}"
                        if not os.path.exists(f"{dirPath}/static/img/mediaImages/Actor_{actorName}.webp"):
                            with open(f"{dirPath}/static/img/mediaImages/Actor_{actorName}.png", "wb") as f:
                                f.write(requests.get(actorImage).content)
                            try:
                                img = Image.open(f"{dirPath}/static/img/mediaImages/Actor_{actorName}.png")
                                img = img.save(f"{dirPath}/static/img/mediaImages/Actor_{actorName}.webp", "webp")
                                os.remove(f"{dirPath}/static/img/mediaImages/Actor_{actorName}.png")
                            except Exception as e:
                                os.rename(f"{dirPath}/static/img/mediaImages/Actor_{actorName}.png", f"{dirPath}/static/img/mediaImages/Actor_{actorName}.webp")

                        actorImage = f"/static/img/mediaImages/Actor_{actorName}.webp"
                        actor = [cast.name, characterName, actorImage, cast.id]
                        if actor not in theCast:
                            theCast.append(actor)
                        else:
                            break
                        person = Person()
                        p = person.details(cast.id)
                        exists = Actors.query.filter_by(actorId=cast.id).first() is not None
                        if not exists:
                            actor = Actors(name=cast.name, actorImage=actorImage, actorDescription=p.biography, actorBirthDate=p.birthday, actorBirthPlace=p.place_of_birth, actorPrograms=f"{movieId}", actorId=cast.id)
                            db.session.add(actor)
                            db.session.commit()
                        else:
                            actor = Actors.query.filter_by(actorId=cast.id).first()
                            actor.actorPrograms = f"{actor.actorPrograms} {movieId}"
                            db.session.commit()
                    theCast = theCast
                    try:
                        date = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y")
                    except ValueError as e:
                        date = "Unknown"
                    except UnboundLocalError:
                        date = "Unknown"

                    genre = res.genre_ids
                    video_path = f"{path}\{originalMovieTitle}"
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
                        if int(seconds) < 10:
                            seconds = f"0{seconds}"
                        length = f"{minutes}:{seconds}"
                    elif len(length) == 1:
                        seconds = str(round(float(length[0])))
                        if int(seconds) < 10:
                            seconds = f"0{seconds}"
                        length = f"00:{seconds}"
                    else:
                        length = "0"

                    duration = length

                    for genreId in genre:
                        if genreList[genreId] not in genresUsed:
                            genresUsed.append(genreList[genreId])
                        if genreList[genreId] not in moviesGenre:
                            moviesGenre.append(genreList[genreId])
                    movieGenre = []
                    for genreId in genre:
                        movieGenre.append(genreList[genreId])

                    bandeAnnonce = details.videos.results
                    bandeAnnonceUrl = ""
                    if len(bandeAnnonce) > 0:
                        for video in bandeAnnonce:
                            bandeAnnonceType = video.type
                            bandeAnnonceHost = video.site
                            bandeAnnonceKey = video.key
                            if bandeAnnonceType == "Trailer":
                                try:
                                    bandeAnnonceUrl = (
                                        websitesTrailers[bandeAnnonceHost] + bandeAnnonceKey
                                    )
                                    break
                                except KeyError as e:
                                    bandeAnnonceUrl = "Unknown"
                                    print(e)
                    alternativesNames = []
                    actualTitle = movieTitle
                    characters = [" ", "-", "_", ":", ".", ",", "!", "'", "`", "\""]
                    empty = ""
                    for character in characters:
                        for character2 in characters:
                            if character != character2:
                                stringTest = actualTitle.replace(character, character2)
                                alternativesNames.append(stringTest)
                                stringTest = actualTitle.replace(character2, character)
                                alternativesNames.append(stringTest)
                                stringTest = actualTitle.replace(character, empty)
                                alternativesNames.append(stringTest)
                                stringTest = actualTitle.replace(character2, empty)
                                alternativesNames.append(stringTest)
                                
                    officialAlternativeNames = movie.alternative_titles(movie_id=movieId).titles
                    if officialAlternativeNames is not None:
                        for officialAlternativeName in officialAlternativeNames:
                            alternativesNames.append(officialAlternativeName.title)

                    alternativesNames = list(dict.fromkeys(alternativesNames))

                    alternativesNames = ",".join(alternativesNames)
                    filmData = Movies(movieId, movieTitle, name, movieCoverPath, banniere, originalMovieTitle, description, note, date, json.dumps(movieGenre), str(duration), json.dumps(theCast), bandeAnnonceUrl, str(res["adult"]), libraryName=libraryName, alternativesNames=alternativesNames, vues=str({}))
                    db.session.add(filmData)
                    db.session.commit()
        elif searchedFilm.endswith("/") == False:
            allMoviesNotSorted.append(searchedFilm)

    movies = Movies.query.filter_by(libraryName=libraryName).all()
    moviesPath = os.listdir(path)
    for movie in movies:
        if movie.slug not in moviesPath:
            db.session.delete(movie)
            db.session.commit()


def getSeries(libraryName):
    allSeriesPath = Libraries.query.filter_by(libName=libraryName).first().libFolder

    try:
        allSeries = [name for name in os.listdir(allSeriesPath) if os.path.isdir(os.path.join(allSeriesPath, name)) and name.endswith((".rar", ".zip", ".part")) == False]
    except OSError as e:
        print("No series found")
        return
    allSeasonsAppelations = ["S"]
    allEpisodesAppelations = ["E"]
    allSeriesDictTemp = {}
    for series in allSeries:
        uglySeasonAppelations = ["Saison", "Season", series.replace(" ", ".")]
        seasons = os.listdir(f"{allSeriesPath}\\{series}")
        serieSeasons = {}
        for season in seasons:
            path = f"{allSeriesPath}\\{series}"
            if (
                not (
                    season.startswith(tuple(allSeasonsAppelations))
                    and not season.endswith(
                        ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")
                    )
                )
                or season.startswith(tuple(uglySeasonAppelations))
                and season.endswith((".rar", ".zip", ".part")) == False
            ):
                allSeasons = os.listdir(f"{path}")
                for allSeason in allSeasons:
                    if ((allSeason.startswith(tuple(allSeasonsAppelations)) == False and allSeason.endswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")) == False) or season.startswith(tuple(uglySeasonAppelations))):
                        if os.path.isdir(f"{path}/{allSeason}") and not (allSeason.startswith(tuple(allSeasonsAppelations)) and allSeason.endswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9"))):
                            print(f"For {uglySeasonAppelations[2]} : {allSeason}")
                            reponse = ask(
                                f"I found that folder, can I rename it from {allSeason} to S{allSeasons.index(allSeason)+1}",
                                AskResult.YES,
                            )
                            if reponse:
                                try:
                                    os.rename(
                                        f"{path}/{allSeason}",
                                        f"{path}/S{allSeasons.index(allSeason)+1}",
                                    )
                                except Exception as e:
                                    print(f"Something went wrong : {e}")
                            else:
                                renameNewName = input("In what do you want rename this folder ? ex: S7, S22...")
                                if renameNewName.isnumeric():
                                    renameNewName = f"S{renameNewName}"
                                elif renameNewName.startswith("S"):
                                    renameNewName=renameNewName
                                try:
                                    os.rename(
                                        f"{path}/{allSeason}",
                                        f"{path}/{renameNewName}",
                                    )
                                except Exception as e:
                                    print(f"Something went wrong : {e}")



            episodesPath = f"{path}\{season}"
            try:
                seasonNumber = season.split(" ")[1]
            except Exception as e:
                seasonNumber = season.replace("S", "")
            if os.path.isdir(episodesPath):
                episodes = os.listdir(episodesPath)
                seasonEpisodes = {}
                oldIndex = 0
                for episode in episodes:
                    episodeName, episodeExtension = os.path.splitext(episode)
                    if os.path.isfile(f"{episodesPath}/{episode}"):
                        if episodeName.startswith(
                            tuple(allEpisodesAppelations)
                        ) and episodeName.endswith(
                            ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")
                        ):
                            oldIndex = episodes.index(episode)
                        else:
                            actualName = f"{episodesPath}/{episode}"
                            oldIndex = episodes.index(episode)
                            if episode.endswith((".rar", ".zip", ".part")) == False:
                                newName = f"E{episodes.index(episode)+1}{episodeExtension}"
                                reponse = ask(
                                    f"Can i rename {actualName} to {episodesPath}/{newName}",
                                    AskResult.YES,
                                )
                                if reponse:
                                    try:
                                        os.rename(
                                            actualName,
                                            f"{episodesPath}/{newName}",
                                        )
                                        episode = f"{newName}"
                                    except Exception as e:
                                        print(f"Something went wrong : {e}")
                                else:
                                    renameNewName = input("In what do you want rename this file ? ex: E7, E22...")
                                    if renameNewName.isnumeric():
                                        renameNewName = f"E{renameNewName}"
                                    elif renameNewName.startswith("E"):
                                        renameNewName=renameNewName
                                    try:
                                        os.rename(
                                            actualName,
                                            f"{episodesPath}/{renameNewName}{episodeExtension}",
                                        )
                                        episode = f"{renameNewName}{episodeExtension}"
                                    except Exception as e:
                                        print(f"Something went wrong : {e}")



                        seasonEpisodes[oldIndex + 1] = f"{path}/{season}/{episode}"
                serieSeasons[seasonNumber] = seasonEpisodes
        serieData = {}
        serieData["seasons"] = serieSeasons
        allSeriesDictTemp[series] = serieData
    allSeriesName = []
    allSeries = allSeriesDictTemp
    for series in allSeries:
        allSeriesName.append(series)
        for season in allSeries[series]["seasons"]:
            for episode in allSeries[series]["seasons"][season]:
                actualPath = allSeries[series]["seasons"][season][episode]
                HTTPPath = actualPath.replace(allSeriesPath, "")
                HTTPPath = HTTPPath.replace("\\", "/")
    
    for serie in allSeriesName:
        if not isinstance(serie, str):
            print(f"{serie} is not 'isinstance'")
            continue
        index = allSeriesName.index(serie) + 1
        percentage = index * 100 / len(allSeriesName)

        loadingFirstPart = ("•" * int(percentage * 0.2))[:-1]
        loadingFirstPart = f"{loadingFirstPart}➤"
        loadingSecondPart = "•" * (20 - int(percentage * 0.2))
        loading = f"{str(int(percentage)).rjust(3)}% | [\33[32m{loadingFirstPart} \33[31m{loadingSecondPart}\33[0m] | {serie} | {index}/{len(allSeriesName)}                              "
        print("\033[?25l", end="")
        print(loading, end="\r", flush=True)
        with app.app_context():

            show = TV()
            serieTitle = serie
            originalSerieTitle = serieTitle
            try:
                serieModifiedTime = os.path.getmtime(f"{allSeriesPath}\\{originalSerieTitle}")
            except FileNotFoundError:
                continue
            try:
                search = show.search(serieTitle)
            except TMDbException as e:
                allSeriesNotSorted.append(serieTitle)
                break

            if not search:
                allSeriesNotSorted.append(serieTitle)
                print(f"{originalSerieTitle} return nothing, try to rename it, the english name return more results.")
                continue

            askForGoodSerie = config["ChocolateSettings"]["askWhichSerie"]
            if askForGoodSerie == "false" or len(search)==1:
                bestMatch = search[0]
                for i in range(len(search)):
                    if (
                        lev(serieTitle, search[i].name) < lev(serieTitle, bestMatch.name)
                        and bestMatch.name not in allSeriesName
                    ):
                        bestMatch = search[i]
                    elif (
                        lev(serieTitle, search[i].name) == lev(serieTitle, bestMatch.name)
                        and bestMatch.name not in allSeriesName
                    ):
                        bestMatch = bestMatch
                    if (
                        lev(serieTitle, bestMatch.name) == 0
                        and bestMatch.name not in allSeriesName
                    ):
                        break
            else:
                print(f"I found {len(search)} series that can be the one you want")
                for serieSearched in search:
                    indexOfTheSerie = search.index(serieSearched)
                    print(f"{serieSearched.name} id:{indexOfTheSerie}")
                valueSelected = int(input("Which serie is it (id):"))
                if valueSelected < len(search):
                    bestMatch = search[valueSelected]

            res = bestMatch
            serieId = res.id


            exists = db.session.query(Series).filter_by(id=serieId).first() is not None
            if not exists:
                details = show.details(serieId)
                seasonsInfo = details.seasons
                name = res.name
                serieCoverPath = f"https://image.tmdb.org/t/p/original{res.poster_path}"
                banniere = f"https://image.tmdb.org/t/p/original{res.backdrop_path}"
                rewritedName = serieTitle.replace(" ", "_")
                if not os.path.exists(f"{dirPath}/static/img/mediaImages/{rewritedName}_Cover.png"):
                    with open(f"{dirPath}/static/img/mediaImages/{rewritedName}_Cover.png","wb") as f:
                        f.write(requests.get(serieCoverPath).content)

                    img = Image.open(f"{dirPath}/static/img/mediaImages/{rewritedName}_Cover.png")
                    img = img.save(f"{dirPath}/static/img/mediaImages/{rewritedName}_Cover.webp", "webp")
                    os.remove(f"{dirPath}/static/img/mediaImages/{rewritedName}_Cover.png")

                if not os.path.exists(f"{dirPath}/static/img/mediaImages/{rewritedName}_Banner.png"):
                    with open(f"{dirPath}/static/img/mediaImages/{rewritedName}_Banner.png","wb") as f:
                        f.write(requests.get(banniere).content)

                    img = Image.open(f"{dirPath}/static/img/mediaImages/{rewritedName}_Banner.png")
                    img = img.save(f"{dirPath}/static/img/mediaImages/{rewritedName}_Banner.webp", "webp")
                    os.remove(f"{dirPath}/static/img/mediaImages/{rewritedName}_Banner.png")
                banniere = f"/static/img/mediaImages/{rewritedName}_Banner.webp"
                serieCoverPath = f"/static/img/mediaImages/{rewritedName}_Cover.webp"
                description = res["overview"]
                note = res.vote_average
                date = res.first_air_date
                serieId = res.id
                details = show.details(serieId)
                seasonsInfo = details.seasons
                cast = details.credits.cast
                runTime = details.episode_run_time
                duration = ""
                for i in range(len(runTime)):
                    if i != len(runTime) - 1:
                        duration += f"{str(runTime[i])}:"
                    else:
                        duration += f"{str(runTime[i])}"
                seasonsInfo = details.seasons
                serieGenre = details.genres
                bandeAnnonce = details.videos.results
                bandeAnnonceUrl = ""
                if len(bandeAnnonce) > 0:
                    for video in bandeAnnonce:
                        bandeAnnonceType = video.type
                        bandeAnnonceHost = video.site
                        bandeAnnonceKey = video.key
                        if bandeAnnonceType == "Trailer" or len(bandeAnnonce) == 1:
                            try:
                                bandeAnnonceUrl = (websitesTrailers[bandeAnnonceHost] + bandeAnnonceKey
                                )
                                break
                            except KeyError as e:
                                bandeAnnonceUrl = "Unknown"
                                print(e)
                genreList = []
                for genre in serieGenre:
                    genreList.append(str(genre.name))
                newCast = []
                cast = list(cast)[:5]
                for actor in cast:
                    actorName = actor.name.replace(" ", "_").replace("/", "")
                    actorImage = f"https://image.tmdb.org/t/p/original{actor.profile_path}"
                    if not os.path.exists(f"{dirPath}/static/img/mediaImages/Actor_{actorName}.webp"):
                        with open(f"{dirPath}/static/img/mediaImages/Actor_{actorName}.png", "wb") as f:
                            f.write(requests.get(actorImage).content)
                        img = Image.open(f"{dirPath}/static/img/mediaImages/Actor_{actorName}.png")
                        img = img.save(f"{dirPath}/static/img/mediaImages/Actor_{actorName}.webp", "webp")
                        os.remove(f"{dirPath}/static/img/mediaImages/Actor_{actorName}.png")

                    actorImage = f"/static/img/mediaImages/Actor_{actorName}.webp"
                    actorCharacter = actor.character
                    actor.profile_path = str(actorImage)
                    actorName = actorName.replace("_", " ")
                    thisActor = [str(actorName), str(actorCharacter), str(actorImage), str(actor.id)]
                    newCast.append(thisActor)

                    
                    person = Person()
                    p = person.details(actor.id)
                    exists = Actors.query.filter_by(actorId=actor.id).first() is not None
                    if not exists:
                        actor = Actors(name=actor.name, actorId=actor.id, actorImage=actorImage, actorDescription=p.biography, actorBirthDate=p.birthday, actorBirthPlace=p.place_of_birth, actorPrograms=f"{serieId}")
                        db.session.add(actor)
                        db.session.commit()
                    else:
                        actor = Actors.query.filter_by(actorId=actor.id).first()
                        actor.actorPrograms = f"{actor.actorPrograms} {serieId}"
                        db.session.commit()

                newCast = json.dumps(newCast[:5])
                genreList = json.dumps(genreList)
                isAdult = str(details["adult"])
                serieObject = Series(id=serieId, name=name, originalName=originalSerieTitle, genre=genreList, duration=duration, description=description, cast=newCast, bandeAnnonceUrl=bandeAnnonceUrl, serieCoverPath=serieCoverPath, banniere=banniere, note=note, date=date, serieModifiedTime=serieModifiedTime, adult=isAdult, libraryName=libraryName)
                db.session.add(serieObject)
                db.session.commit()
                seasonsNumber = []
                seasons = os.listdir(f"{allSeriesPath}/{originalSerieTitle}")
                for season in seasons:
                    season = re.sub(r"\D", "", season)
                    seasonsNumber.append(int(season))


                for season in seasonsInfo:
                    releaseDate = season.air_date
                    episodesNumber = season.episode_count
                    seasonNumber = season.season_number
                    seasonId = season.id
                    seasonName = season.name
                    
                    try:
                        exists = Seasons.query.filter_by(seasonId=seasonId).first() is not None
                    except sqlalchemy.exc.PendingRollbackError as e:
                        db.session.rollback()
                        exists = Seasons.query.filter_by(seasonId=seasonId).first() is not None
                    if not exists and seasonNumber in seasonsNumber:
                        seasonDescription = season.overview
                        seasonCoverPath = (f"https://image.tmdb.org/t/p/original{season.poster_path}")
                        if not os.path.exists(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.png"):
                            with open(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.png", "wb") as f:
                                f.write(requests.get(seasonCoverPath).content)
                            img = Image.open(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.png")
                            img = img.save(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.webp", "webp")
                            os.remove(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.png")

                        seasonCoverPath = f"/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.webp"

                        allSeasonsUglyDict = os.listdir(f"{allSeriesPath}/{serie}")
                        try:
                            allSeasons = [int(season.replace("S", "")) for season in allSeasonsUglyDict]
                        except ValueError as e:
                            break
                        
                        try:
                            modifiedDate = os.path.getmtime(f"{allSeriesPath}/{serie}/S{seasonNumber}")
                        except FileNotFoundError as e:
                            continue

                        thisSeason = Seasons(serie=serieId, release=releaseDate, episodesNumber=episodesNumber, seasonNumber=seasonNumber, seasonId=seasonId, seasonName=seasonName, seasonDescription=seasonDescription, seasonCoverPath=seasonCoverPath, modifiedDate=modifiedDate)
                        
                        try:
                            db.session.add(thisSeason)
                            db.session.commit()
                        except sqlalchemy.exc.PendingRollbackError as e:
                            db.session.rollback()
                            db.session.add(thisSeason)
                            db.session.commit()
                        
                        try:
                            allEpisodes = os.listdir(f"{allSeriesPath}/{serie}/S{seasonNumber}")
                        except FileNotFoundError as e:
                            continue

                        for episode in allEpisodes:
                            slug = f"/{serie}/S{seasonNumber}/{episode}"
                            episodeName = slug.split("/")[-1]
                            episodeName, extension = os.path.splitext(episodeName)

                            try:
                                episodeIndex = int(episodeName.replace("E", ""))
                            except:
                                break
                            showEpisode = Episode()
                            try:
                                episodeInfo = showEpisode.details(serieId, seasonNumber, episodeIndex)
                                exists = Episodes.query.filter_by(episodeId=episodeInfo.id).first() is not None
                                if not exists:
                                    coverEpisode = f"https://image.tmdb.org/t/p/original{episodeInfo.still_path}"
                                    rewritedName = originalSerieTitle.replace(" ", "_")
                                    if not os.path.exists(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.png"):
                                        with open(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.png","wb") as f:
                                            f.write(requests.get(coverEpisode).content)

                                        img = Image.open(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.png")
                                        img = img.save(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.webp", "webp")
                                        os.remove(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.png")
                                    coverEpisode = f"/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.webp"

                                    try:
                                        episodeData = Episodes(episodeId=episodeInfo.id, episodeName=episodeName, seasonId=seasonId, episodeNumber=episodeIndex, episodeDescription=episodeInfo.overview, episodeCoverPath=coverEpisode, releaseDate=episodeInfo.air_date, slug=slug, introStart=0.0, introEnd=0.0)
                                        db.session.add(episodeData)
                                        db.session.commit()
                                    except:
                                        pass
                            except TMDbException as e:
                                print(f"I didn't find an the episode {episodeIndex} of the season {seasonNumber} of the serie with ID {serieId}",e)

                            

            else:
                seasonsNumber = []
                seasons = os.listdir(f"{allSeriesPath}/{originalSerieTitle}")
                for season in seasons:
                    season = re.sub(r"\D", "", season)
                    seasonsNumber.append(int(season))
                theSerie = Series.query.filter_by(id=serieId).first()
                theSerieModifiedTime = theSerie.serieModifiedTime
                if serieModifiedTime > theSerieModifiedTime:
                    theSerie.serieModifiedTime = serieModifiedTime
                    db.session.commit()
                details = show.details(serieId)
                seasonsInfo = details.seasons

                for season in seasonsInfo:
                    releaseDate = season.air_date
                    episodesNumber = season.episode_count
                    seasonNumber = season.season_number
                    seasonId = season.id
                    seasonName = season.name
                    
                    try:
                        exists = Seasons.query.filter_by(seasonId=seasonId).first() is not None
                    except sqlalchemy.exc.PendingRollbackError as e:
                        db.session.rollback()
                        exists = Seasons.query.filter_by(seasonId=seasonId).first() is not None
                    if not exists and seasonNumber in seasonsNumber:
                        seasonDescription = season.overview
                        seasonCoverPath = (f"https://image.tmdb.org/t/p/original{season.poster_path}")
                        if not os.path.exists(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.png"):
                            with open(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.png", "wb") as f:
                                f.write(requests.get(seasonCoverPath).content)
                            img = Image.open(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.png")
                            img = img.save(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.webp", "webp")
                            os.remove(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.png")

                        seasonCoverPath = f"/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.webp"

                        allSeasonsUglyDict = os.listdir(f"{allSeriesPath}/{serie}")
                        try:
                            allSeasons = [int(season.replace("S", "")) for season in allSeasonsUglyDict]
                        except ValueError as e:
                            break
                        
                        try:
                            modifiedDate = os.path.getmtime(f"{allSeriesPath}/{serie}/S{seasonNumber}")
                        except FileNotFoundError as e:
                            break
                        
                        thisSeason = Seasons(serie=serieId, release=releaseDate, episodesNumber=episodesNumber, seasonNumber=seasonNumber, seasonId=seasonId, seasonName=seasonName, seasonDescription=seasonDescription, seasonCoverPath=seasonCoverPath, modifiedDate=modifiedDate)
                        
                        try:
                            db.session.add(thisSeason)
                            db.session.commit()
                        except sqlalchemy.exc.PendingRollbackError as e:
                            db.session.rollback()
                            db.session.add(thisSeason)
                            db.session.commit()
                    elif seasonNumber in seasonsNumber:
                        thisSeason = Seasons.query.filter_by(seasonId=seasonId).first()
                        modifiedDate = os.path.getmtime(f"{allSeriesPath}/{serie}/S{seasonNumber}")
                        modifiedDateDB = thisSeason.modifiedDate
                        if modifiedDate > modifiedDateDB:
                            thisSeason.modifiedDate = modifiedDate
                            db.session.commit()

                            try:
                                allEpisodes = os.listdir(f"{allSeriesPath}/{serie}/S{seasonNumber}")
                            except FileNotFoundError as e:
                                continue

                            for episode in allEpisodes:

                                slug = f"/{serie}/S{seasonNumber}/{episode}"
                                episodeName = slug.split("/")[-1]
                                episodeName, extension = os.path.splitext(episodeName)

                                try:
                                    episodeIndex = int(episodeName.replace("E", ""))
                                except:
                                    break
                                showEpisode = Episode()
                                try:
                                    episodeInfo = showEpisode.details(serieId, seasonNumber, episodeIndex)
                                    exists = Episodes.query.filter_by(episodeId=episodeInfo.id).first() is not None
                                    if not exists:
                                        coverEpisode = f"https://image.tmdb.org/t/p/original{episodeInfo.still_path}"
                                        rewritedName = originalSerieTitle.replace(" ", "_")
                                        if not os.path.exists(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.png"):
                                            with open(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.png","wb") as f:
                                                f.write(requests.get(coverEpisode).content)
                                            img = Image.open(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.png")
                                            img = img.save(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.webp", "webp")
                                            os.remove(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.png")
                                        coverEpisode = f"/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.webp"

                                        try:
                                            episodeData = Episodes(episodeId=episodeInfo.id, episodeName=episodeName, seasonId=seasonId, episodeNumber=episodeIndex, episodeDescription=episodeInfo.overview, episodeCoverPath=coverEpisode, releaseDate=episodeInfo.air_date, slug=slug, introStart=0.0, introEnd=0.0)
                                            db.session.add(episodeData)
                                            db.session.commit()
                                        except:
                                            pass
                                except TMDbException as e:
                                    print(f"I didn't find an the episode {episodeIndex} of the season {seasonNumber} of the serie with ID {serieId}",e)

def getGames(libraryName):
    allGamesPath = Libraries.query.filter_by(libName=libraryName).first().libFolder
    try:
        allConsoles = [name for name in os.listdir(allGamesPath) if os.path.isdir(os.path.join(allGamesPath, name)) and name.endswith((".rar", ".zip", ".part")) == False]
        for console in allConsoles:
            if os.listdir(f"{allGamesPath}/{console}") == []:
                allConsoles.remove(console)

    except OSError as e:
        print("No games found")
        return
    saidPS1 = False
    supportedConsoles = ['3DO', 'Amiga', 'Atari 2600', 'Atari 5200', 'Atari 7800', 'Atari Jaguar', 'Atari Lynx', 'GB', 'GBA', 'GBC', 'N64', 'NDS', 'NES', 'SNES', 'Neo Geo Pocket', 'PSX', 'Sega 32X', 'Sega CD', 'Sega Game Gear', 'Sega Master System', 'Sega Mega Drive', 'Sega Saturn', "PS1"]
    supportedFileTypes = [".zip", ".adf", ".adz", ".dms", ".fdi", ".ipf", ".hdf", ".lha", ".slave", ".info", ".cdd", ".nrg", ".mds", ".chd", ".uae", ".m3u", ".a26", ".a52", ".a78", ".j64", ".lnx", ".gb", ".gba", ".gbc", ".n64", ".nds", ".nes", ".ngp", ".psx", ".sfc", ".smc", ".smd", ".32x", ".cd", ".gg", ".md", ".sat", ".sms"]
    for console in allConsoles:
        if console not in supportedConsoles:
            print(f"{console} is not supported or the console name is not correct, here is the list of supported consoles : {', '.join(supportedConsoles)} rename the folder to one of these names if it's the correct console")
            break
        size = len(allConsoles)
        gameName, extension = os.path.splitext(console)
        index = allConsoles.index(console) + 1
        percentage = index * 100 / size

        loadingFirstPart = ("•" * int(percentage * 0.2))[:-1]
        loadingFirstPart = f"{loadingFirstPart}➤"
        loadingSecondPart = "•" * (20 - int(percentage * 0.2))
        loading = f"{str(int(percentage)).rjust(3)}% | [\33[32m{loadingFirstPart} \33[31m{loadingSecondPart}\33[0m] | {gameName} | {index}/{len(allConsoles)}                                                      "
        print("\033[?25l", end="")
        print(loading, end="\r", flush=True)
        allFiles = os.listdir(allGamesPath)
        for file in allFiles:
            with app.app_context():
                exists = Games.query.filter_by(slug=f"{allGamesPath}/{console}/{file}").first() is not None
                if file.endswith(tuple(supportedFileTypes)) and exists == None:
                    
                    newFileName = file                    
                    newFileName = re.sub(r'\d{5} - ', '', newFileName)
                    newFileName = re.sub(r'\d{4} - ', '', newFileName)
                    newFileName = re.sub(r'\d{3} - ', '', newFileName)
                    newFileName, extension = os.path.splitext(newFileName)
                    newFileName = newFileName.rstrip()
                    newFileName = f"{newFileName}{extension}"
                    os.rename(f"{allGamesPath}/{console}/{file}", f"{allGamesPath}/{console}/{newFileName}")
                    file = newFileName
                    while ".." in newFileName:
                        newFileName = newFileName.replace("..", ".")
                    try:
                        os.rename(f"{allGamesPath}/{console}/{file}", f"{allGamesPath}/{console}/{newFileName}")
                    except FileExistsError:
                        os.remove(f"{allGamesPath}/{console}/{file}")
                    file, extension = os.path.splitext(file)

                    gameIGDB = searchGame(file, console)
                    if gameIGDB != None and gameIGDB != {} and not exists:
                        gameName = gameIGDB["title"]
                        gameRealTitle = newFileName
                        gameCover = gameIGDB["cover"]
                        gameDescription = gameIGDB["description"]
                        gameNote = gameIGDB["note"]
                        gameDate = gameIGDB["date"]
                        gameGenre = gameIGDB["genre"]
                        gameId = gameIGDB["id"]
                        gameConsole = console
                        gameSlug = f"{allGamesPath}/{console}/{newFileName}"
                        game = Games(console=gameConsole, id=gameId, title=gameName, realTitle=gameRealTitle, cover=gameCover, description=gameDescription, note=gameNote, date=gameDate, genre=gameGenre, slug=gameSlug, libraryName=libraryName)
                        db.session.add(game)
                        db.session.commit()
                    else:
                        print(f"I didn't find the game {file} at {console}")
                elif console == "PS1" and file.endswith(".cue") and exists == None:
                    if saidPS1 == False:
                        print(f"You need to zip all our .bin files and the .cue file in one .zip file to being able to play it")
                        saidPS1 = True
                        
                    value = config["ChocolateSettings"]["compressPS1Games"]
                    if value.lower() == "true":
                        
                        index = allFiles.index(file)-1
                        
                        allBins = []
                        while allFiles[index].endswith(".bin"):
                            allBins.append(allFiles[index])
                            index -= 1
                            
                        fileName, extension = os.path.splitext(file)
                        with zipfile.ZipFile(f"{allGamesPath}/{console}/{fileName}.zip", 'w') as zipObj:
                            for binFiles in allBins:
                                zipObj.write(f"{allGamesPath}/{console}/{binFiles}", binFiles)
                            zipObj.write(f"{allGamesPath}/{console}/{file}", file)
                        for binFiles in allBins:
                            os.remove(f"{allGamesPath}/{console}/{binFiles}")
                        os.remove(f"{allGamesPath}/{console}/{file}")
                        file = f"{fileName}.zip"
                        newFileName = file                    
                        newFileName = re.sub(r'\d{5} - ', '', newFileName)
                        newFileName = re.sub(r'\d{4} - ', '', newFileName)
                        newFileName = re.sub(r'\d{3} - ', '', newFileName)
                        newFileName, extension = os.path.splitext(newFileName)
                        newFileName = newFileName.rstrip()
                        newFileName = f"{newFileName}{extension}"
                        os.rename(f"{allGamesPath}/{console}/{file}", f"{allGamesPath}/{console}/{newFileName}")
                        file = newFileName
                        while ".." in newFileName:
                            newFileName = newFileName.replace("..", ".")
                        try:
                            os.rename(f"{allGamesPath}/{console}/{file}", f"{allGamesPath}/{console}/{newFileName}")
                        except FileExistsError:
                            os.remove(f"{allGamesPath}/{console}/{file}")
                        file, extension = os.path.splitext(file)

                        gameIGDB = searchGame(file, console)
                        if gameIGDB != None and gameIGDB != {}:
                            gameName = gameIGDB["title"]
                            gameRealTitle = newFileName
                            gameCover = gameIGDB["cover"]
                            
                            with open(f"{allGamesPath}/{console}/{gameRealTitle}.png", 'wb') as f:
                                f.write(requests.get(gameCover).content)
                            gameCover = f"{allGamesPath}/{console}/{gameRealTitle}.png"
                            img = Image.open(gameCover)
                            img = img.save(f"{allGamesPath}/{console}/{gameRealTitle}.webp", "webp")
                            os.remove(gameCover)
                            gameCover = f"{allGamesPath}/{console}/{gameRealTitle}.webp"

                            gameDescription = gameIGDB["description"]
                            gameNote = gameIGDB["note"]
                            gameDate = gameIGDB["date"]
                            gameGenre = gameIGDB["genre"]
                            gameId = gameIGDB["id"]
                            gameConsole = console
                            gameSlug = f"{allGamesPath}/{console}/{newFileName}"
                            exists = Games.query.filter_by(slug=gameSlug).first()
                            if exists == None:
                                game = Games(console=gameConsole, id=gameId, title=gameName, realTitle=gameRealTitle, cover=gameCover, description=gameDescription, note=gameNote, date=gameDate, genre=gameGenre, slug=gameSlug)
                                db.session.add(game)
                                try:
                                    db.session.commit()
                                except IntegrityError as e:
                                    e=e
                                    db.session.commit()
                        

                elif not file.endswith(".bin") and exists == None:
                    print(f"{file} is not supported, here's the list of supported files : \n{','.join(supportedFileTypes)}")

def length_video(path: str) -> float:
    seconds = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            path,
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    return float(seconds.stdout)



def getGpuInfo() -> str:
    if platform.system() == "Windows":
        return gpuname()
    elif platform.system() == "Darwin":
        return subprocess.check_output(
            ["/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string"]
        ).strip()
    elif platform.system() == "Linux":
        return "impossible d'accéder au GPU"
    return ""


def gpuname() -> str:
    """Returns the model name of the first available GPU"""
    try:
        gpus = GPUtil.getGPUs()
    except:
        print("Unable to detect GPU model. Is your GPU configured? Are you running with nvidia-docker?")
        return "UNKNOWN"
    if len(gpus) == 0:
        raise ValueError("No GPUs detected in the system")
    return gpus[0].name

@app.before_request
def before_request():
    libraries = Libraries.query.all()
    libraries = [library.__dict__ for library in libraries]
    users = Users.query.all()
    for library in libraries:
        del library["_sa_instance_state"]
    
    #get username with Flask-
    if current_user.is_authenticated:
        username = current_user.name
        for library in libraries:
            if library["availableFor"] != None:
                availableFor = library["availableFor"].split(",")
                if username not in availableFor:
                    libraries.remove(library)

    libraries = sorted(libraries, key=lambda k: k['libName'])
    libraries = sorted(libraries, key=lambda k: k['libType'])

    g.libraries = libraries
    g.users = users

@app.route("/video/<id>", methods=["GET"])
def create_m3u8(id):
    movie = Movies.query.filter_by(id=id).first()
    slug = movie.slug
    library = movie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    video_path = f"{path}/{slug}"
    duration = length_video(video_path)

    allAudioTracks = """"""
    languages = {
        "eng": "English",
        "fre": "French",
        "spa": "Spanish",
        "ger": "German",
        "ita": "Italian",
        "jpn": "Japanese",
        "por": "Portuguese",
        "rus": "Russian",
        "kor": "Korean",
    }
    #extract audio tracks
    audioTracks = subprocess.run([ "ffprobe", "-v", "error", "-show_entries", "stream=index:stream_tags=language", "-of", "compact=p=0:nk=1", video_path], stdout=subprocess.PIPE, text=True)
    audioTracks = audioTracks.stdout.split("\n")
    for audioTrack in audioTracks:
        try:
            language = audioTrack.split("|")[1]
            index = audioTrack.split("|")[0]
            if index == 0:
                default = "YES"
            else:
                default = "NO"
            allAudioTracks += f"#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID='audio',NAME='{languages[language]}',DEFAULT={default},AUTOSELECT=YES,LANGUAGE='{language}',URI='/audio/{id}/{index}.m3u8'\n"
        except:
            pass

    file = f"""
#EXTM3U

{allAudioTracks}

#EXT-X-VERSION:4
#EXT-X-TARGETDURATION:5
#EXT-X-MEDIA-SEQUENCE:1
"""

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""
#EXTINF:5.0,
/chunk/{id}-{(i // CHUNK_LENGTH) + 1}.ts
"""

    file += """
#EXT-X-ENDLIST"
"""

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", f"http://{local_ip}:{serverPort}")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{id}.m3u8"
    )

    return response

@app.route("/video/<quality>/<id>", methods=["GET"])
def create_m3u8_quality(quality, id):
    movie = Movies.query.filter_by(id=id).first()
    slug = movie.slug
    library = movie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    video_path = f"{path}/{slug}"
    duration = length_video(video_path)
    file = """
    #EXTM3U
    #EXT-X-VERSION:4
    #EXT-X-TARGETDURATION:5
    #EXT-X-MEDIA-SEQUENCE:1
    """

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""
        #EXTINF:5.0,
        /chunk/{quality}/{id}-{(i // CHUNK_LENGTH) + 1}.ts
        """

    file += """
    #EXT-X-ENDLIST"
    """

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", f"http://{local_ip}:{serverPort}")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{id}.m3u8"
    )

    return response

@app.route("/videoSerie/<episodeId>", methods=["GET"])
def create_serie_m3u8(episodeId):
    episode = Episodes.query.filter_by(episodeId=episodeId).first()
    season = Seasons.query.filter_by(seasonId=episode.seasonId).first()
    serie = Series.query.filter_by(id=season.serie).first()
    library = serie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    episodePath = episode.slug
    episodePath = episodePath.replace("/", "\\")
    episodePath = f"{path}{episodePath}"
    duration = length_video(episodePath)
    file = """
    #EXTM3U
    #EXT-X-VERSION:4
    #EXT-X-TARGETDURATION:5
    #EXT-X-MEDIA-SEQUENCE:1
    """

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""
        #EXTINF:5.0,
        /chunkSerie/{episodeId}-{(i // CHUNK_LENGTH) + 1}.ts
        """

    file += """
    #EXT-X-ENDLIST"
    """

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", f"http://{local_ip}:{serverPort}")
    response.headers.set("Content-Disposition", "attachment", filename=f"{episodeId}")

    return response

@app.route("/videoSerie/<quality>/<episodeId>", methods=["GET"])
def create_serie_m3u8_quality(quality, episodeId):
    episode = Episodes.query.filter_by(episodeId=episodeId).first()
    season = Seasons.query.filter_by(seasonId=episode.seasonId).first()
    serie = Series.query.filter_by(id=season.serie).first()
    library = serie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    episodePath = episode.slug
    episodePath = episodePath.replace("/", "\\")
    episodePath = f"{path}{episodePath}"
    duration = length_video(episodePath)
    file = """
    #EXTM3U
    #EXT-X-VERSION:4
    #EXT-X-TARGETDURATION:5
    #EXT-X-MEDIA-SEQUENCE:1
    """

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""
        #EXTINF:5.0,
        /chunkSerie/{quality}/{episodeId}-{(i // CHUNK_LENGTH) + 1}.ts
        """

    file += """
    #EXT-X-ENDLIST"
    """

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", f"http://{local_ip}:{serverPort}")
    response.headers.set("Content-Disposition", "attachment", filename=f"{episodeId}")

    return response

@app.route("/chunkSerie/<episodeId>-<int:idx>.ts", methods=["GET"])
def get_chunk_serie(episodeId, idx=0):
    seconds = (idx - 1) * CHUNK_LENGTH
    episode = Episodes.query.filter_by(episodeId=episodeId).first()
    season = Seasons.query.filter_by(seasonId=episode.seasonId).first()
    serie = Series.query.filter_by(id=season.serie).first()
    library = serie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    episodePath = episode.slug
    episodePath = episodePath.replace("/", "\\")
    episodePath = f"{path}{episodePath}"

    time_start = str(datetime.timedelta(seconds=seconds))
    time_end = str(datetime.timedelta(seconds=seconds + CHUNK_LENGTH))
    logLevelValue = "error"
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        logLevelValue,
        "-ss",
        time_start,
        "-to",
        time_end,
        "-i",
        episodePath,
        "-output_ts_offset",
        time_start,
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-ac",
        "2",
        "-preset",
        "ultrafast",
        "-f",
        "mpegts",
        "pipe:1",
    ]

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", f"http://{local_ip}:{serverPort}")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{episodeId}-{idx}.ts"
    )

    return response

@app.route("/chunkSerie/<quality>/<episodeId>-<int:idx>.ts", methods=["GET"])
def get_chunk_serie_quality(quality, episodeId, idx=0):
    seconds = (idx - 1) * CHUNK_LENGTH
    episode = Episodes.query.filter_by(episodeId=episodeId).first()
    season = Seasons.query.filter_by(seasonId=episode.seasonId).first()
    serie = Series.query.filter_by(id=season.serie).first()
    library = serie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    episodePath = episode.slug
    episodePath = episodePath.replace("/", "\\")
    episodePath = f"{path}{episodePath}"

    time_start = str(datetime.timedelta(seconds=seconds))
    time_end = str(datetime.timedelta(seconds=seconds + CHUNK_LENGTH))
    videoProperties = get_video_properties(episodePath)
    width = videoProperties["width"]
    height = videoProperties["height"]
    newWidth = float(quality)
    newHeight = round(float(width) / float(height) * newWidth)
    if (newHeight % 2) != 0:
        newHeight += 1
    logLevelValue = "error"
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        logLevelValue,
        "-ss",
        time_start,
        "-to",
        time_end,
        "-i",
        episodePath,
        "-output_ts_offset",
        time_start,
        "-c:v",
        "libx264",
        "-vf",
        f"scale={newHeight}:{newWidth}",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-ac",
        "2",
        "-preset",
        "ultrafast",
        "-f",
        "mpegts",
        "pipe:1",
    ]



    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", f"http://{local_ip}:{serverPort}")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{episodeId}-{idx}.ts"
    )

    return response


@app.route("/chunk/<id>-<int:idx>.ts", methods=["GET"])
def get_chunk(id, idx=0):
    global movieExtension
    seconds = (idx - 1) * CHUNK_LENGTH
    movie = Movies.query.filter_by(id=id).first()
    slug = movie.slug
    library = movie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    video_path = f"{path}/{slug}"

    time_start = str(datetime.timedelta(seconds=seconds))
    time_end = str(datetime.timedelta(seconds=seconds + CHUNK_LENGTH))
    logLevelValue = "error"
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        logLevelValue,
        "-ss",
        time_start,
        "-to",
        time_end,
        "-i",
        video_path,
        "-output_ts_offset",
        time_start,
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-ac",
        "2",
        "-preset",
        "ultrafast",
        "-f",
        "mpegts",
        "pipe:1",
    ]



    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", f"http://{local_ip}:{serverPort}")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{id}-{idx}.ts"
    )

    return response

@app.route("/chunk/<quality>/<id>-<int:idx>.ts", methods=["GET"])
def get_chunk_quality(quality, id, idx=0):
    seconds = (idx - 1) * CHUNK_LENGTH

    movie = Movies.query.filter_by(id=id).first()
    slug = movie.slug
    library = movie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    video_path = f"{path}/{slug}"

    time_start = str(datetime.timedelta(seconds=seconds))
    time_end = str(datetime.timedelta(seconds=seconds + CHUNK_LENGTH))
    videoProperties = get_video_properties(video_path)
    width = videoProperties["width"]
    height = videoProperties["height"]
    newWidth = float(quality)
    newHeight = round(float(width) / float(height) * newWidth)
    if (newHeight % 2) != 0:
        newHeight += 1
    logLevelValue = "error"
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        logLevelValue,
        "-ss",
        time_start,
        "-to",
        time_end,
        "-i",
        video_path,
        "-output_ts_offset",
        time_start,
        "-c:v",
        "libx264",
        "-vf",
        f"scale={newHeight}:{newWidth}",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-ac",
        "2",
        "-preset",
        "ultrafast",
        "-f",
        "mpegts",
        "pipe:1",
    ]

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", f"http://{local_ip}:{serverPort}")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{id}-{idx}.ts"
    )

    return response

@app.route("/chunkCaption/<language>/<index>/<id>.vtt", methods=["GET"])
def chunkCaption(id, language, index):
    movie = Movies.query.filter_by(id=id).first()
    slug = movie.slug
    library = movie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    video_path = f"{path}/{slug}"

    extractCaptionsCommand = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        video_path,
        "-map",
        f"0:{index}",
        "-f",
        "webvtt",
        "pipe:1",
    ]


    extractCaptions = subprocess.run(extractCaptionsCommand, stdout=subprocess.PIPE)

    extractCaptionsResponse = make_response(extractCaptions.stdout)
    extractCaptionsResponse.headers.set("Content-Type", "text/VTT")
    extractCaptionsResponse.headers.set(
        "Content-Disposition", "attachment", filename=f"{language}/{index}/{id}.vtt"
    )

    return extractCaptionsResponse

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        accountName = request.form["name"]
        accountPassword = request.form["password"]
        try:
            f = request.files['profilePicture']
            name, extension = os.path.splitext(f.filename)
            thisdirPath = dirPath.replace("\\", "//")
            f.save(f"{thisdirPath}/static/img/{accountName}{extension}")
            profilePicture = f"/static/img/{accountName}{extension}"
            if extension == "":
                profilePicture = "/static/img/defaultUserProfilePic.png"
        except:
            profilePicture = "/static/img/defaultUserProfilePic.png"
        accountTypeInput = request.form["type"]

        if accountTypeInput == "Kid":
            accountPassword = ""

        new_user = Users(name=accountName, password=accountPassword, profilePicture=profilePicture, accountType=accountTypeInput)
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError as e:
            e=e
            db.session.commit()
        login_user(new_user)
        if accountTypeInput == "Admin":
            return redirect(url_for("settings"))
        else:
            return redirect(url_for("home"))
    if request.method == "GET":
        typeOfUser = current_user.accountType
        if typeOfUser == "Admin":
            global allMoviesNotSorted
            condition = len(allMoviesNotSorted) > 0
            return render_template("settings.html", notSorted=allMoviesNotSorted, conditionIfOne=condition)
        else:
            return redirect(url_for("home"))

@app.route("/login", methods=["GET", "POST"])
def login():
    allUsers = Users.query.filter().all()
    allUsersDict = []
    for user in allUsers:
        userDict = {"name": user.name, "profilePicture": user.profilePicture, "accountType": user.accountType}
        allUsersDict.append(userDict)
    
    if len(allUsersDict)==0:
        return redirect(url_for("createAccount"))
    if request.method == "POST":
        accountName = request.form["name"]
        accountPassword = request.form["password"]
        user = Users.query.filter_by(name=accountName).first()
        if user:
            if user.verify_password(accountPassword):
                login_user(user)

                return redirect(url_for("home"))
            elif user.accountType == "Kid":
                login_user(user)
                return redirect(url_for("home"))
            else:
                return "Wrong password"
        else:
            return "Wrong username"
    return render_template("login.html", allUsers=allUsersDict)

@app.route("/createAccount", methods=["POST", "GET"])
def createAccount():
    allUsers = Users.query.filter().all()
    allUsersDict = []
    for user in allUsers:
        userDict = {"name": user.name, "profilePicture": user.profilePicture}
        allUsersDict.append(userDict)
    
    if len(allUsersDict)>0:
        return redirect(url_for("home"))

    if request.method == "POST":
        accountName = request.form["name"]
        accountPassword = request.form["password"]
        try:
            f = request.files['profilePicture']
            name, extension = os.path.splitext(f.filename)
            thisdirPath = dirPath.replace("\\", "//")
            profilePicture = f"/static/img/{accountName}{extension}"
            if extension == "":
                profilePicture = "/static/img/defaultUserProfilePic.png"
            else:
                f.save(f"{thisdirPath}{profilePicture}")
        except:
            profilePicture = "/static/img/defaultUserProfilePic.png"

        accountTypeInput = request.form["type"]
        new_user = Users(name=accountName, password=accountPassword, profilePicture=profilePicture, accountType=accountTypeInput)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        if accountTypeInput == "Admin":
            return redirect(url_for("settings"))
        else:
            return redirect(url_for("home"))
    return render_template("createAccount.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/profil", methods=["GET", "POST"])
def profil():
    user = current_user
    currentUsername = user.name
    if request.method == "POST":
        userName = request.form["name"]
        password = request.form["password"]
        try:
            f = request.files['profilePicture']
            name, extension = os.path.splitext(f.filename)
            thisdirPath = dirPath.replace("\\", "//")
            profilePicture = f"/static/img/{userName}{extension}"
            if extension == "":
                profilePicture = "/static/img/defaultUserProfilePic.png"
        except:
            profilePicture = "/static/img/defaultUserProfilePic.png"
        userToEdit = Users.query.filter_by(name=currentUsername).first()
        if userToEdit.name != userName:
            userToEdit.name = userName
            logout_user()
            db.session.commit()
        if userToEdit.password != generate_password_hash(password) and len(password)>0:
            userToEdit.password = generate_password_hash(password)
            db.session.commit()
        if userToEdit.profilePicture != profilePicture and profilePicture != "/static/img/defaultUserProfilePic.png":
            f = request.files['profilePicture']
            f.save(f"{thisdirPath}{profilePicture}")
            userToEdit.profilePicture = profilePicture
            db.session.commit()
    return render_template("profil.html", user=user)

@app.route("/getAccountType", methods=["GET", "POST"])
def getAccountType():
    user = current_user
    return json.dumps({"accountType": user.accountType})


@app.route("/chunkCaptionSerie/<language>/<index>/<episodeId>.vtt", methods=["GET"])
def chunkCaptionSerie(language, index, episodeId):
    episode = Episodes.query.filter_by(episodeId=episodeId).first()
    season = Seasons.query.filter_by(seasonId=episode.seasonId).first()
    serie = Series.query.filter_by(id=season.serie).first()
    library = serie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    episodePath = episode.slug
    episodePath = episodePath.replace("/", "\\")
    video_path = f"{path}{episodePath}"

    extractCaptionsCommand = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        video_path,
        "-map",
        f"0:{index}",
        "-f",
        "webvtt",
        "pipe:1",
    ]


    extractCaptions = subprocess.run(extractCaptionsCommand, stdout=subprocess.PIPE)

    extractCaptionsResponse = make_response(extractCaptions.stdout)
    extractCaptionsResponse.headers.set("Content-Type", "text/VTT")
    extractCaptionsResponse.headers.set(
        "Content-Disposition", "attachment", filename=f"{language}/{index}/{episodeId}.vtt"
    )

    return extractCaptionsResponse

@app.route("/saveSettings", methods=["POST"])
def saveSettings():
    language = request.form["language"]
    discordRPC = request.form["discordRPCCheckbox"]
    port = request.form["port"]
    if language != "":
        config.set("ChocolateSettings", "language", language)
    if port != "" or port != " ":
        config.set("ChocolateSettings", "port", port)
    if discordRPC == "on":
        config.set("ChocolateSettings", "discordrpc", "true")
    else:
        config.set("ChocolateSettings", "discordrpc", "false")
    with open(os.path.join(dir, 'config.ini'), "w") as conf:
        config.write(conf)
    return redirect(url_for("settings"))



@app.route("/getAllMovies/<library>", methods=["GET"])
def getAllMovies(library):
    movies = Movies.query.filter_by(libraryName=library).all()
    moviesDict = [ movie.__dict__ for movie in movies ]
    user = current_user
    userType = user.accountType
    for movie in moviesDict:
        del movie["_sa_instance_state"]
    
    if userType in ["Kid", "Teen"]:
        for movie in moviesDict:
            if movie["adult"] == "True":
                moviesDict.remove(movie)

    moviesDict = sorted(moviesDict, key=lambda k: k['realTitle'])

    return json.dumps(moviesDict, ensure_ascii=False)

@app.route("/createLib", methods=["POST"])
def createLib():
    theRequest = request.get_json()
    libName = theRequest["libName"]
    libPath = theRequest["libPath"].replace("/", "\\")
    libType = theRequest["libType"]
    libUsers = theRequest["libUsers"]

    if libUsers == "":
        libUsers = None

    icons = {
        "movies": "videocam",
        "series": "tv",
        "games": "game-controller"
        }

    libPath = libPath.replace("/", "\\")

    exists = Libraries.query.filter_by(libName=libName).first() is not None
    if not exists:
        newLib = Libraries(libName=libName, libFolder=libPath, libType=libType, libImage=icons[libType], availableFor=libUsers)
        db.session.add(newLib)
        db.session.commit()
        return json.dumps({"error": "worked"})
    else:
        return json.dumps({"error": "The library already exists"})

@app.route("/getAllSeries/<library>", methods=["GET"])
def getAllSeries(library):
    series = Series.query.filter_by(libraryName=library).all()
    series = [ serie.__dict__ for serie in series ]
    user = current_user
    userType = user.accountType
    if userType in ["Kid", "Teen"]:
        for serie in series:
            if serie["adult"] == "True":
                series.remove(serie)
                
    seriesDict = { serie.name: dict(serie.__dict__) for serie in series }

    return json.dumps(seriesDict, ensure_ascii=False, default=str, indent=4)

def getSimilarMovies(movieId):
    global searchedFilms
    similarMoviesPossessed = []
    movie = Movie()
    similarMovies = movie.recommendations(movieId)
    for movieInfo in similarMovies:
        movieName = movieInfo.title
        for movie in searchedFilms:
            if movieName == movie:
                similarMoviesPossessed.append(movie)
                break
    return similarMoviesPossessed


def getSimilarSeries(seriesId) -> list:
    global allSeriesDict
    similarSeriesPossessed = []
    show = TV()
    similarSeries = show.recommendations(seriesId)
    for serieInfo in similarSeries:
        serieName = serieInfo.name
        for serie in allSeriesDict:
            try:
                if serieName == allSeriesDict[serie]["name"]:
                    similarSeriesPossessed.append(allSeriesDict[serie])
                    break
            except KeyError as e:
                print(e)
                pass
    return similarSeriesPossessed


@app.route("/getMovieData/<movieId>", methods=["GET", "POST"])
def getMovieData(movieId):
    exists = db.session.query(Movies).filter_by(id=movieId).first() is not None
    if exists:
        movie = Movies.query.filter_by(id=movieId).first().__dict__
        del movie["_sa_instance_state"]
        movie["similarMovies"] = getSimilarMovies(movieId)
        return json.dumps(movie, ensure_ascii=False)
    else:
        return json.dumps("Not Found", ensure_ascii=False)


@app.route("/getSerieData/<serieId>", methods=["GET", "POST"])
def getSeriesData(serieId):
    exists = db.session.query(Series).filter_by(id=serieId).first() is not None
    if exists:
        serie = Series.query.filter_by(id=serieId).first().__dict__
        serie["seasons"] = getSerieSeasons(serie["id"])
        del serie["_sa_instance_state"]
        return json.dumps(serie, ensure_ascii=False)

def getSerieSeasons(id):
    seasons = Seasons.query.filter_by(serie=id).all()
    seasonsDict = {}
    for season in seasons:
        seasonsDict[season.seasonNumber] = dict(season.__dict__)
        del seasonsDict[season.seasonNumber]["_sa_instance_state"]
    return seasonsDict

@app.route("/")
@app.route("/index")
@app.route("/home")
@login_required
def home():
    return render_template("index.html")

@app.route("/season/<theId>")
@login_required
def season(theId):
    with app.app_context():
        season = Seasons.query.filter_by(seasonId=theId).first()
        season = season.__dict__
        serie = Series.query.filter_by(id=int(season["serie"])).first()
        serie = serie.__dict__
        serie = serie["name"]
        name = f"{serie} | {season['seasonName']}"
        del season["_sa_instance_state"]
        return render_template("season.html", serie=season, title=name)


@app.route("/getSeasonData/<seasonId>/", methods=["GET", "POST"])
def getSeasonData(seasonId):
    global allSeriesDict
    season = Seasons.query.filter_by(seasonId=seasonId).first()
    episodes = Episodes.query.filter_by(seasonId=seasonId).all()
    episodesDict = {}
    for episode in episodes:
        episodesDict[episode.episodeNumber] = dict(episode.__dict__)
        del episodesDict[episode.episodeNumber]["_sa_instance_state"]
    season = season.__dict__
    del season["_sa_instance_state"]
    season["episodes"] = episodesDict
    return json.dumps(season, ensure_ascii=False, default=str)

@app.route("/getEpisodeData/<serieName>/<seasonId>/<episodeId>/", methods=["GET", "POST"])
def getEpisodeData(serieName, seasonId, episodeId):
    global allSeriesDict
    seasonId = seasonId.replace("S", "")
    episodeId = episodeId
    if serieName in allSeriesDict.keys():
        data = allSeriesDict[serieName]
        season = data["seasons"][seasonId]
        episode = season["episodes"][str(episodeId)]
        return json.dumps(episode, ensure_ascii=False, default=str)
    else:
        response = {"response": "Not Found"}
        return json.dumps(response, ensure_ascii=False, default=str)


@app.route("/movies/<library>")
@login_required
def library(library):
    if library != "undefined":
        thisLibrary = Libraries.query.filter_by(libName=library).first()
        movies = Movies.query.all()
        moviesDict = [ movie.__dict__ for movie in movies ]
        for movie in moviesDict:
            del movie["_sa_instance_state"]
        searchedFilmsUp0 = len(moviesDict) == 0
        errorMessage = "Verify that the path is correct, or restart Chocolate"
        routeToUse = f"/getAllMovies/{thisLibrary.libName}"
        return render_template("allFilms.html",
            conditionIfOne=searchedFilmsUp0,
            errorMessage=errorMessage,
            routeToUse=routeToUse,
        )
    else:
        return "Not Found"


@app.route("/series/<library>")
@login_required
def seriesLibrary(library):
    series = Series.query.filter_by(libraryName=library).all()
    seriesDict = { serie.name: dict(serie.__dict__) for serie in series }
    searchedSeriesUp0 = len(seriesDict.keys()) == 0
    errorMessage = "Verify that the path is correct, or restart Chocolate"
    routeToUse = f"/getAllSeries/{library}"
    return render_template("allSeries.html",conditionIfOne=searchedSeriesUp0, errorMessage=errorMessage, routeToUse=routeToUse)

@app.route("/games/<library>")
@login_required
def games(library):
    games = Games.query.filter_by(libraryName=library).all()
    gamesDict = [ game.__dict__ for game in games ]
    searchedGamesUp0 = len(gamesDict) == 0
    errorMessage = "Verify that the path is correct, or restart Chocolate"
    routeToUse = f"/getAllGames/{library}"
    return render_template("consoles.html")
    
@app.route("/getAllConsoles/<library>")
def getAllConsoles(library):
    consoles = Games.query.filter_by(libraryName=library).all()
    consolesDict = [ console.__dict__ for console in consoles ]
    for console in consolesDict:
        del console["_sa_instance_state"]
        for key in list(console.keys()):
            if key != "console":
                del console[key]
    consolesDict = [i for n, i in enumerate(consolesDict) if i not in consolesDict[n + 1:]]
    consolesDict = [list(i.values())[0] for i in consolesDict]
    consolesDict = sorted(consolesDict)
    return json.dumps(consolesDict, ensure_ascii=False, default=str)

@app.route("/getConsoleData/<consoleName>")
def getConsoleData(consoleName):
    consolesData = {
        "GB": { "name": "Gameboy", "image": "/static/img/Gameboy.png" },
        "GBA": { "name": "Gameboy Advance", "image": "/static/img/Gameboy Advance.png" },
        "GBC": { "name": "Gameboy Color", "image": "/static/img/Gameboy Color.png" },
        "N64": { "name": "Nintendo 64", "image": "/static/img/N64.png" },
        "NES": { "name": "Nintendo Entertainment System", "image": "/static/img/NES.png" },
        "NDS": { "name": "Nintendo DS", "image": "/static/img/Nintendo DS.png" },
        "SNES": { "name": "Super Nintendo Entertainment System", "image": "/static/img/SNES.png" },
        "Sega Mega Drive": { "name": "Sega Mega Drive", "image": "/static/img/Sega Mega Drive.png" },
        "Sega Master System": { "name": "Sega Master System", "image": "/static/img/Sega Master System.png" },
        "Sega Saturn": { "name": "Sega Saturn", "image": "/static/img/Sega Saturn.png" },
        "PS1": { "name": "PS1", "image": "/static/img/PS1.png" },
    }
    return json.dumps(consolesData[consoleName], ensure_ascii=False, default=str)

consoles = {"Gameboy": "GB", "Gameboy Advance": "GBA", "Gameboy Color": "GBC", "Nintendo 64": "N64", "Nintendo Entertainment System": "NES", "Nintendo DS": "NDS", "Super Nintendo Entertainment System": "SNES", "Sega Mega Drive": "Sega Mega Drive", "Sega Master System": "Sega Master System", "Sega Saturn": "Sega Saturn", "PS1": "PS1"}
        
@app.route("/console/<library>/<consoleName>")
@login_required
def console(library, consoleName):
    if consoleName != "undefined":
        consoleName = consoleName.replace("%20", " ")
        global consoles
        games = Games.query.filter_by(console=consoles[consoleName], libraryName=library).all()
        gamesDict = [ game.__dict__ for game in games ]
        for game in gamesDict:
            del game["_sa_instance_state"]
        searchedGamesUp0 = len(gamesDict) == 0
        errorMessage = "Verify that the games path is correct"
        
        routeToUse = "/getAllGames"
        return render_template("games.html",
            conditionIfOne=searchedGamesUp0,
            errorMessage=errorMessage,
            routeToUse=routeToUse,
            consoleName=consoleName
        )
    else:
        return json.dumps({"response": "Not Found"}, ensure_ascii=False, default=str)

@app.route("/getGames/<consoleName>")
def getGamesFor(consoleName):
    if consoleName != None:
        consoleName = consoleName.replace("%20", " ")
        global consoles
        games = Games.query.filter_by(console=consoles[consoleName]).all()
        gamesDict = [ game.__dict__ for game in games ]
        for game in gamesDict:
            del game["_sa_instance_state"]
        return json.dumps(gamesDict, ensure_ascii=False, default=str)
    else:
        return json.dumps({"response": "Not Found"}, ensure_ascii=False, default=str)

@app.route("/game/<console>/<gameSlug>")
@login_required
def game(console, gameSlug):
    if console != None:
        consoleName = console.replace("%20", " ")
        gameSlug = gameSlug.replace("%20", " ")
        global consoles
        game = Games.query.filter_by(console=consoles[consoleName], realTitle=gameSlug).first()
        game = game.__dict__
        gameFileName, gameExtension = os.path.splitext(gameSlug)
        slug = f"/gameFile/{game['console']}/{game['realTitle']}"
        bios = f"/bios/{consoleName}"
        del game["_sa_instance_state"]
        scripts = {
            "Gameboy": f'<script type="text/javascript">\nEJS_player = "#game";\nEJS_biosUrl = "";\nEJS_gameUrl = "{slug}";\nEJS_core = "gb";\n</script>',
            "Gameboy Advance": f'<script type="text/javascript">\nEJS_player = "#game";\nEJS_biosUrl = "";\nEJS_gameUrl = "{slug}";\nEJS_core = "gba";\n</script>',
            "Gameboy Color": f'<script type="text/javascript">\nEJS_player = "#game";\nEJS_biosUrl = "";\nEJS_gameUrl = "{slug}";\nEJS_core = "gb";\n</script>',
            "Nintendo 64": f'<script type="text/javascript">\nEJS_player = "#game";\nEJS_gameUrl = "{slug}";\nEJS_core = "n64";\n</script>',
            "Nintendo Entertainment System": f'<script type="text/javascript">\nEJS_player = "#game";\nEJS_biosUrl = "";\nEJS_gameUrl = "{slug}";\nEJS_core = "nes";\nEJS_lightgun = false;\n</script>',
            "Nintendo DS": f'<script type="text/javascript">\nEJS_player = "#game";\nEJS_biosUrl = "";\nEJS_gameUrl = "{slug}";\nEJS_core = "nds";\n</script>',
            "Super Nintendo Entertainment System": f'<script type="text/javascript">\nEJS_player = "#game";\nEJS_biosUrl = "";\nEJS_gameUrl = "{slug}";\nEJS_core = "snes";\nEJS_mouse = false;\nEJS_multitap = false;\n</script>',
            "Sega Mega Drive": f'<script type="text/javascript">\nEJS_player = "#game";\nEJS_gameUrl = "{slug}";\nEJS_core = "segaMD";\n</script>',
            "Sega Master System": f'<script type="text/javascript">\nEJS_player = "#game";\nEJS_gameUrl = "{slug}";\nEJS_core = "segaMS";\n</script>',
            "Sega Saturn": f'<script type="text/javascript">\nEJS_player = "#game";\nEJS_biosUrl = "";\nEJS_gameUrl = "{slug}";\nEJS_core = "segaSaturn";\n</script>',
            "PS1": f'<script type="text/javascript">\nEJS_player = "#game";\nEJS_biosUrl = "{bios}";\nEJS_gameUrl = "{slug}";\nEJS_core = "psx";\n</script>',
        }
        theScript = scripts[consoleName]
        theScript = Markup(theScript)
        return render_template("game.html", script=theScript, gameName=game["title"], consoleName=consoleName)

@app.route("/gameFile/<console>/<gameSlug>")
def gameFile(console, gameSlug):
    if console != None:
        consoleName = console.replace("%20", " ")
        gameSlug = gameSlug.replace("%20", " ")
        game = Games.query.filter_by(console=consoleName, realTitle=gameSlug).first()
        game = game.__dict__
        slug = game["slug"]
        return send_file(slug, as_attachment=True)

@app.route("/bios/<console>")
def bios(console):
    if console != None:
        consoleName = console.replace("%20", " ")
        Bios = [i for i in os.listdir(f"{dirPath}/static/bios/{consoleName}") if i.endswith(".bin")]
        Bios = f"{dirPath}/static/bios/{consoleName}/{Bios[0]}"

        return send_file(Bios, as_attachment=True)

@app.route("/searchInMovies/<library>/<search>")
@login_required
def searchInAllMovies(library, search):
    search = search.replace("%20", " ")
    movies = Movies.query.filter_by(libraryName=library).all()
    #SELECT * FROM Movies WHERE ((title, realTitle,slug,description,cast,date,genre) like %search%)
    movies = [m for m in movies if any(search.lower() in x.lower() for x in (m.title.lower(), m.realTitle.lower(), m.slug.lower(), m.description.lower(), m.cast.lower(), m.date.lower(), m.genre.lower(), m.alternativesNames.lower()))]
    movies = [i.__dict__ for i in movies]
    for i in movies:
        del i["_sa_instance_state"]
    user = current_user
    userType = user.accountType
    
    if userType in ["Kid", "Teen"]:
        for movie in movies:
            if movie["adult"] == "True":
                movies.remove(movie)
    return json.dumps(movies, ensure_ascii=False)


@app.route("/searchInSeries/<library>/<search>")
@login_required
def searchInAllSeries(library, search):
    search = search.replace("%20", " ")
    series = Series.query.filter_by(libraryName=library).all()
    #SELECT * FROM Series WHERE ((name, originalName,description,cast,date) like %search%)    
    series = [m for m in series if any(search in x.lower() for x in (m.name, m.originalName, m.description, m.cast, m.date, m.genre))]
    series = [i.__dict__ for i in series]
    for serie in series:
        del serie["_sa_instance_state"]
    user = current_user
    userType = user.accountType
    
    if userType in ["Kid", "Teen"]:
        for serie in series:
            if serie["adult"] == "True":
                series.remove(serie)
    return json.dumps(series, ensure_ascii=False)


@app.route("/search/<library>/<search>")
@login_required
def search(library, search):
    library = library.replace("%20", " ")
    theLibrary = Libraries.query.filter_by(libName=library).first()
    theLibrary = theLibrary.__dict__
    if theLibrary["libType"] == "movies":
        searchedFilmsUp0 = False
        errorMessage = "Verify your search terms"
        routeToUse = f"/searchInMovies/{library}/{search}"
        return render_template("allFilms.html",
            conditionIfOne=searchedFilmsUp0,
            errorMessage=errorMessage,
            routeToUse=routeToUse,
        )
    elif theLibrary["libType"] == "series":
        searchedFilmsUp0 = False
        errorMessage = "Verify your search terms"
        routeToUse = f"/searchInSeries/{library}/{search}"
        return render_template("allSeries.html",
            conditionIfOne=searchedFilmsUp0,
            errorMessage=errorMessage,
            routeToUse=routeToUse,
        )


@app.route("/movie/<id>")
@login_required
def movie(id):
    global movieExtension, searchedFilms
    if not id.endswith("ttf"):
        movie = Movies.query.filter_by(id=id).first()
        slug = movie.slug
        rewriteSlug, movieExtension = os.path.splitext(slug)
        link = f"/video/{id}".replace(" ", "%20")
        link1080 = f"/video/1080/{id}".replace(" ", "%20")
        link720 = f"/video/720/{id}".replace(" ", "%20")
        link480 = f"/video/480/{id}".replace(" ", "%20")
        link360 = f"/video/360/{id}".replace(" ", "%20")
        link240 = f"/video/240/{id}".replace(" ", "%20")
        link144 = f"/video/144/{id}".replace(" ", "%20")
        allCaptions = generateCaptionMovie(id)
        title = rewriteSlug
        return render_template(
        "film.html", slug=slug, movieUrl=link, allCaptions=allCaptions, title=title, movieUrl1080=link1080, movieUrl720=link720, movieUrl480=link480, movieUrl360=link360, movieUrl240=link240, movieUrl144=link144)
    return "Shut up and take my money !"

@app.route("/setVuesTimeCode/", methods=["POST"])
@login_required
def setVuesTimeCode():
    data = request.get_json()
    movieID = data["movieID"]
    timeCode = data["timeCode"]
    username = current_user.name
    movie = Movies.query.filter_by(id=movieID).first()
    actualVues = movie.vues

    actualVues = ast.literal_eval(actualVues)
    
    actualVues[username] = timeCode

    actualVues = str(actualVues)
    movie.vues = actualVues
    db.session.commit()
    return "ok"

@app.route("/whoami", methods=["GET"])
@login_required
def whoami():
    return json.dumps(current_user.name)

@app.route("/serie/<episodeId>")
@login_required
def serie(episodeId):
    global allSeriesDict
    if episodeId.endswith("ttf"):
        pass
    else:
        thisEpisode = Episodes.query.filter_by(episodeId=episodeId).first().__dict__
        del thisEpisode["_sa_instance_state"]
        seasonId = thisEpisode["seasonId"]
        slug = thisEpisode["slug"]
        episodeName = thisEpisode["episodeName"]
        slugUrl = slug.split("/")[-1]
        link = f"/videoSerie/{episodeId}".replace(" ", "%20")
        link1080 = f"/videoSerie/1080/{episodeId}".replace(" ", "%20")
        link720 = f"/videoSerie/720/{episodeId}".replace(" ", "%20")
        link480 = f"/videoSerie/480/{episodeId}".replace(" ", "%20")
        link360 = f"/videoSerie/360/{episodeId}".replace(" ", "%20")
        link240 = f"/videoSerie/240/{episodeId}".replace(" ", "%20")
        link144 = f"/videoSerie/144/{episodeId}".replace(" ", "%20")
        allCaptions = generateCaptionSerie(episodeId)
        episodeId = int(episodeId)
        episodes = Episodes.query.filter_by(seasonId=seasonId).all()
        episodes = sorted(episodes, key=lambda x: x.episodeNumber)
        firstEpisode = episodes[0].episodeNumber
        lastEpisode = episodes[-1].episodeNumber
        theActualEpisodes = thisEpisode["episodeNumber"]
        previousEpisode = episodes[theActualEpisodes-2]
        try:
            nextEpisode = episodes[theActualEpisodes]
        except:
            nextEpisode = None

        buttonNext = theActualEpisodes < lastEpisode
        buttonPrevious = theActualEpisodes > firstEpisode

        buttonPreviousHREF = f"/serie/{previousEpisode.episodeId}"
        try:
            buttonNextHREF = f"/serie/{nextEpisode.episodeId}"
        except:
            buttonNextHREF = None
        return render_template("serie.html", slug=slug, movieUrl=link, allCaptions=allCaptions, title=episodeName, buttonNext=buttonNext, buttonPrevious=buttonPrevious, buttonNextHREF=buttonNextHREF, buttonPreviousHREF=buttonPreviousHREF, movieUrl1080=link1080, movieUrl720=link720, movieUrl480=link480, movieUrl360=link360, movieUrl240=link240, movieUrl144=link144)
    return "Error"

def generateCaptionSerie(episodeId):
    episode = Episodes.query.filter_by(episodeId=episodeId).first()
    season = Seasons.query.filter_by(seasonId=episode.seasonId).first()
    serie = Series.query.filter_by(id=season.serie).first()
    library = serie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    episodePath = episode.slug
    episodePath = episodePath.replace("/", "\\")
    slug = f"{path}{episodePath}"
    captionCommand = [
        "ffprobe",
        "-loglevel",
        "error",
        "-select_streams",
        "s",
        "-show_entries",
        "stream=index:stream_tags=language",
        "-of",
        "csv=p=0",
        slug,
    ]
    captionPipe = subprocess.Popen(captionCommand, stdout=subprocess.PIPE)
    try:
        slug = slug.split("\\")[-1]
        slug = slug.split("/")[-1]
    except:
        slug = slug.split("/")[-1]
    captionResponse = captionPipe.stdout.read().decode("utf-8")
    captionResponse = captionResponse.split("\n")

    allCaptions = []
    languages = {
        "ara": "Arabic",
        "eng": "English",
        "fre": "Français",
        "spa": "Español",
        "por": "Português",
        "ita": "Italiano",
        "ger": "Deutsch",
        "rus": "Русский",
        "pol": "Polski",
        "por": "Português",
        "chi": "中文",
        "srp": "Srpski",
    }

    captionResponse.pop()

    for line in captionResponse:
        line = line.rstrip()
        language = line.split(",")[1]
        index = line.split(",")[0]
        allCaptions.append(
            {
                "index": index,
                "languageCode": language,
                "language": languages[language],
                "url": f"/chunkCaptionSerie/{language}/{index}/{episodeId}.vtt",
            }
        )
    return allCaptions



def generateCaptionMovie(id):
    movie = Movies.query.filter_by(id=id).first()
    library = movie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    moviePath = movie.slug
    moviePath = moviePath.replace("/", "\\")
    slug = f"{path}\{moviePath}"

    captionCommand = [
        "ffprobe",
        "-loglevel",
        "error",
        "-select_streams",
        "s",
        "-show_entries",
        "stream=index:stream_tags=language",
        "-of",
        "csv=p=0",
        slug,
    ]
    captionPipe = subprocess.Popen(captionCommand, stdout=subprocess.PIPE)
    try:
        slug = slug.split("\\")[-1]
        slug = slug.split("/")[-1]
    except:
        slug = slug.split("/")[-1]
    rewriteSlug, movieExtension = os.path.splitext(slug)
    captionResponse = captionPipe.stdout.read().decode("utf-8")
    captionResponse = captionResponse.split("\n")

    allCaptions = []
    languages = {
        "eng": "English",
        "fre": "Français",
        "spa": "Español",
        "por": "Português",
        "ita": "Italiano",
        "ger": "Deutsch",
        "rus": "Русский",
        "pol": "Polski",
        "por": "Português",
        "chi": "中文",
        "srp": "Srpski",
    }

    captionResponse.pop()
    for line in captionResponse:
        line = line.rstrip()
        try:
            language = line.split(",")[1]
            index = line.split(",")[0]
            allCaptions.append(
                {
                    "index": index,
                    "languageCode": language,
                    "language": languages[language],
                    "url": f"/chunkCaption/{language}/{index}/{id}.vtt",
                }
            )
        except:
            break

    return allCaptions


@app.route("/generateAudio/<slug>")
def generateAudio(slug):
    audioCommand = [
        "ffprobe",
        "-loglevel",
        "error",
        "-select_streams",
        "a",
        "-show_entries",
        "stream=index:stream_tags=language",
        "-of",
        "csv=p=0",
        slug,
    ]
    audioPipe = subprocess.Popen(audioCommand, stdout=subprocess.PIPE)
    try:
        slug = slug.split("\\")[-1]
        slug = slug.split("/")[-1]
    except:
        slug = slug.split("/")[-1]
    rewriteSlug, movieExtension = os.path.splitext(slug)
    audioResponse = audioPipe.stdout.read().decode("utf-8")
    audioResponse = audioResponse.split("\n")
    audioResponse.pop()
    allAudio = []
    languages = {
        "eng": "English",
        "fre": "Français",
        "spa": "Español",
        "por": "Português",
        "ita": "Italiano",
        "ger": "Deutsch",
        "rus": "Русский",
        "pol": "Polski",
        "por": "Português",
        "chi": "中文",
        "srp": "Srpski",
    }
    for line in audioResponse:
        line = line.rstrip()
        language = line.split(",")[1]
        index = line.split(",")[0]
        allAudio.append(
            {
                "index": index,
                "languageCode": language,
                "language": languages[language],
                "url": f"/chunkAudio/{language}/{index}/{rewriteSlug}.mp3",
            }
        )

    return allAudio


@app.route("/actor/<actorId>")
@login_required
def actor(actorId):
    if actorId != "undefined":
        routeToUse = f"/getActorData/{actorId}"
        actor = Actors.query.filter_by(actorId=actorId).first()
        actorName = actor.name
        return render_template("actor.html", routeToUse=routeToUse, actorName=actorName)
    return json.dumps({"error": "undefined"})


@app.route("/getActorData/<actorId>", methods=["GET", "POST"])
def getActorData(actorId):
    moviesData = []
    seriesData = []
    actor = Actors.query.filter_by(actorId=actorId).first()
    movies = actor.actorPrograms.split(" ")
    for movie in movies:
        try:
            thisMovie = Movies.query.filter_by(id=movie).first().__dict__
            del thisMovie["_sa_instance_state"]
            if thisMovie not in moviesData:
                moviesData.append(thisMovie)
        except:
            thisSeries = Series.query.filter_by(id=movie).first().__dict__
            del thisSeries["_sa_instance_state"]
            if thisSeries not in seriesData:
                seriesData.append(thisSeries)
        
    actorData = {
        "actorName": actor.name,
        "actorImage": actor.actorImage,
        "actorDescription": actor.actorDescription,
        "actorBirthday": actor.actorBirthDate,
        "actorBirthplace": actor.actorBirthPlace,
        "actorMovies": moviesData,
        "actorSeries": seriesData,
    }
    return json.dumps(actorData, default=lambda o: o.__dict__, ensure_ascii=False)

@app.route("/getThisEpisodeData/<episodeID>", methods=["GET", "POST"])
def getThisEpisodeData(episodeID):
    episode = Episodes.query.filter_by(episodeId=episodeID).first()
    episodeData = {
        "episodeName": episode.episodeName,
        "introStart": episode.introStart,
        "introEnd": episode.introEnd,
    }
    return json.dumps(episodeData, default=lambda o: o.__dict__, ensure_ascii=False)


@app.route("/scanIntro")
def scanIntro():
    os.system("python intro.py")
    return redirect(url_for("settings"))

@app.route("/isChocolate", methods=["GET", "POST"])
def isChocolate():
    return json.dumps({"isChocolate": True})


def sort_dict_by_key(unsorted_dict):

    sorted_keys = sorted(unsorted_dict.keys(), key=lambda x:x.lower())

    sorted_dict= {}
    for key in sorted_keys:
        sorted_dict.update({key: unsorted_dict[key]})

    return sorted_dict
        

if __name__ == "__main__":
    enabledRPC = config["ChocolateSettings"]["discordrpc"]
    if enabledRPC == "true":
        try:
            RPC.update(
            state="Loading Chocolate...",
            details=f"The Universal MediaManager | v{chocolateVersion} ({lastCommitHash})",
            large_image="loader",
            large_text="Chocolate",
            buttons=[{"label": "Github", "url": "https://github.com/ChocolateApp/Chocolate"}],
            start=start_time)
        except:
            pass
        
    with app.app_context():
        libraries = Libraries.query.all()
        libraries = [library.__dict__ for library in libraries]
        libraries = sorted(libraries, key=lambda k: k['libName'])
        libraries = sorted(libraries, key=lambda k: k['libType'])

        for library in libraries:
            if library["libType"] == "series":
                getSeries(library["libName"])
            elif library["libType"] == "movies":
                getMovies(library["libName"])
            elif library["libType"] == "games":
                getGames(library["libName"])

    print()
    print("\033[?25h", end="")
    
    enabledRPC = config["ChocolateSettings"]["discordrpc"]
    if enabledRPC == "true":
        try:
            RPC.update(
            state="Idling",
            details=f"The Universal MediaManager | v{chocolateVersion} ({lastCommitHash})",
            large_image="largeimage",
            large_text="Chocolate",
            buttons=[{"label": "Github", "url": "https://github.com/ChocolateApp/Chocolate"}],
            start=time.time())
        except:
            pass

    with app.app_context():
        allSeriesDict = {}
        for u in db.session.query(Series).all():
            allSeriesDict[u.name] = u.__dict__

    app.run(host="0.0.0.0", port=serverPort)