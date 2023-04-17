import configparser
import datetime
import json
import os
import platform
import re
import subprocess
import warnings
import zipfile
import zlib
import requests
import rarfile
import pycountry
import PyPDF2
import base64
import io
import git
import GPUtil
import sqlalchemy

from sqlite3 import IntegrityError
from flask import Flask, url_for, request, redirect, make_response, send_file, g, abort, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from tmdbv3api import TMDb, Movie, TV, Episode, Person, Find
from tmdbv3api.as_obj import AsObj
from tmdbv3api.exceptions import TMDbException
from videoprops import get_video_properties
from Levenshtein import distance as lev
from ask_lib import AskResult, ask
from deep_translator import GoogleTranslator
from time import mktime, localtime, time
from PIL import Image
from pypresence import Presence
from uuid import uuid4
from unidecode import unidecode
from pyarr import RadarrAPI, SonarrAPI, LidarrAPI, ReadarrAPI
from guessit import guessit

start_time = mktime(localtime())

with warnings.catch_warnings():
   warnings.simplefilter("ignore", category = sqlalchemy.exc.SAWarning)

app = Flask(__name__)
app.secret_key = "ChocolateDBPassword"

CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

dirPath = os.getcwd()
dirPath = os.path.dirname(__file__).replace("\\", "/")
app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///{dirPath}/database.db'
app.config['MAX_CONTENT_LENGTH'] = 4096 * 4096
app.config['UPLOAD_FOLDER'] = f"{dirPath}/static/img/"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
loginManager = LoginManager()
loginManager.init_app(app)
loginManager.login_view = 'login'
langs_dict = GoogleTranslator().get_supported_languages(as_dict=True)
allAuthTokens = {}

def get_uuid():
    return uuid4().hex

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    profilePicture = db.Column(db.String(255))
    accountType = db.Column(db.String(255))

    def __init__(self, name, password, profilePicture, accountType):
        self.name = name
        if password != None:
            self.password = generate_password_hash(password)
        else:
            self.password = None
        self.profilePicture = profilePicture
        self.accountType = accountType

    def __repr__(self) -> str:
        return f'<Name {self.name}>'

    def verify_password(self, pwd):
        if self.password == None:
            return True
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
    numberOfEpisodeInFolder = db.Column(db.Integer)

    def __init__(self, serie, release, episodesNumber, seasonNumber, seasonId, seasonName, seasonDescription, seasonCoverPath, modifiedDate, numberOfEpisodeInFolder):
        self.serie = serie
        self.release = release
        self.episodesNumber = episodesNumber
        self.seasonNumber = seasonNumber
        self.seasonId = seasonId
        self.seasonName = seasonName
        self.seasonDescription = seasonDescription
        self.seasonCoverPath = seasonCoverPath
        self.modifiedDate = modifiedDate
        self.numberOfEpisodeInFolder = numberOfEpisodeInFolder

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
    

class OthersVideos(db.Model):
    videoHash = db.Column(db.String(255), primary_key=True)
    title = db.Column(db.String(255), primary_key=True)
    slug = db.Column(db.String(255))
    banner = db.Column(db.String(255))
    duration = db.Column(db.String(255))
    libraryName = db.Column(db.String(255))
    vues = db.Column(db.Text, default=str({}))

    def __init__(self, videoHash, title, slug, banner, duration, libraryName, vues):
        self.videoHash = videoHash
        self.title = title
        self.slug = slug
        self.banner = banner
        self.duration = duration
        self.libraryName = libraryName
        self.vues = vues
    
    def __repr__(self) -> str:
        return f"<OthersVideos {self.title}>"

class Books(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255))
    slug = db.Column(db.String(255))
    bookType = db.Column(db.String(255))
    cover = db.Column(db.String(255))
    libraryName = db.Column(db.String(255))

    def __repr__(self) -> str:
        return f"<Books {self.title}>"

    

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
    try:
        db.init_app(app)
    except:
        pass

@loginManager.user_loader
def load_user(id):
    return Users.query.get(int(id))

dir = os.path.dirname(__file__)

config = configparser.ConfigParser()
config.read(os.path.join(dir, 'config.ini'))
if config["ChocolateSettings"]["language"] == "Empty":
    config["ChocolateSettings"]["language"] = "EN"

chocolateVersion = config["ChocolateSettings"]["version"]
try:
    repo = git.Repo(search_parent_directories=True)
    lastCommitHash = repo.head.object.hexsha[:7]
except:
    lastCommitHash = "xxxxxxx"
with app.app_context():
    libraries = Libraries.query.filter_by(libType="games").all() is not None
    if libraries:
        clientID = config.get("APIKeys", "IGDBID")
        clientSecret = config.get("APIKeys", "IGDBSECRET")
        if clientID == "Empty" or clientSecret == "Empty":
            print("Follow this tutorial to get your IGDB API Keys: https://api-docs.igdb.com/#account-creation")

tmdb = TMDb()
apiKeyTMDB = config["APIKeys"]["TMDB"]
if apiKeyTMDB == "Empty":
    print("Follow this tutorial to get your TMDB API Key : https://developers.themoviedb.org/3/getting-started/introduction")
tmdb.api_key = config["APIKeys"]["TMDB"]
tmdb.language = config["ChocolateSettings"]["language"]
with open(os.path.join(dir, 'config.ini'), 'w') as configfile:
    config.write(configfile)


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
            "Accept": "application/json", "Authorization": f"Bearer {token}", "Client-ID": clientID
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
                        "GB": "Game Boy", "GBA": "Game Boy Advance", "GBC": "Game Boy Color", "N64": "Nintendo 64", "NES": "Nintendo Entertainment System", "NDS": "Nintendo DS", "SNES": "Super Nintendo Entertainment System", "Sega Master System": "Sega Master System", "Sega Mega Drive": "Sega Mega Drive", "PS1": "PS1"
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
                        "title": game["name"], "cover": game["cover"]["url"].replace("//", "https://"), "description": game["summary"], "note": game["total_rating"], "date": game["first_release_date"], "genre": genres, "id": game["id"]
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
CHUNK_LENGTH = int(CHUNK_LENGTH)
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
    

    allMoviesNotSorted = []
    movie = Movie()
    path = Libraries.query.filter_by(libName=libraryName).first().libFolder
    filmFileList = []
    try:
        movies = os.listdir(path)
    except:
        return
    for movieFile in movies:
        if not movieFile.endswith((".rar", ".zip", ".part")):
            filmFileList.append(movieFile)

    movies = Movies.query.filter_by(libraryName=libraryName).all()
    moviesPath = os.listdir(path)
    for movie in movies:
        slug = movie.slug
        #print(f"Movie {movie.realTitle} slug: {slug}\n")
        possibleDirSlug = slug.split("/")[0:-1]
        possibleDirSlug = "/".join(possibleDirSlug)
        if slug not in moviesPath and possibleDirSlug == "":
            db.session.delete(movie)
            db.session.commit()
        elif slug not in moviesPath and possibleDirSlug != "":
            path = f"{path}\{possibleDirSlug}\{slug}"
            dirPath = f"{path}\{possibleDirSlug}"
            exist = os.path.exists(path)
            existDir = os.path.exists(dirPath)
            if not exist or not existDir:
                db.session.delete(movie)
                db.session.commit()

    filmFileList.sort()
    dirPath = os.getcwd()
    dirPath = os.path.dirname(__file__).replace("\\", "/")

    for searchedFilm in filmFileList:
        if not isinstance(searchedFilm, str):
            continue
        if True:
            movieTitle = searchedFilm
            if os.path.isdir(os.path.join(path, movieTitle)):
                try:
                    movieTitle = os.listdir(os.path.join(path, movieTitle))[0]
                except Exception as e:
                    print(f"Error with movie {movieTitle} in subfolder: {e}")
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
            slug = searchedFilm
            exists = Movies.query.filter_by(slug=slug).first() is not None
            if not exists:
                movie = Movie()
                try:
                    search = movie.search(movieTitle, adult=True)
                except Exception as e:
                    search = movie.search(movieTitle)
                if not search:
                    guessedData = guessit(movieTitle)
                    if "year" in guessedData:
                        try:
                            search = movie.search(guessedData["title"], year=guessedData["year"], adult=True)
                        except:
                            search = movie.search(guessedData["title"], year=guessedData["year"])
                    else:
                        try:
                            search = movie.search(guessedData["title"], adult=True)
                        except:
                            search = movie.search(guessedData["title"])
                if not search:
                    allMoviesNotSorted.append(originalMovieTitle)
                    continue
                bestMatch = search[0]
                if config["ChocolateSettings"]["askwhichmovie"] == "false" or len(search)==1:
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

                res = bestMatch
                try:
                    name = res.title
                except AttributeError as e:
                    name = res.original_title
                movieId = res.id
                details = movie.details(movieId)
                
                start = ""
                if os.path.isdir(os.path.join(path, searchedFilm)):
                    start = f"{searchedFilm}/"

                movieCoverPath = f"https://image.tmdb.org/t/p/original{res.poster_path}"
                banniere = f"https://image.tmdb.org/t/p/original{res.backdrop_path}"
                realTitle, extension = os.path.splitext(originalMovieTitle)

                with open(f"{dirPath}/static/img/mediaImages/{movieId}_Cover.png", "wb") as f:
                    f.write(requests.get(movieCoverPath).content)
                try:
                    img = Image.open(f"{dirPath}/static/img/mediaImages/{movieId}_Cover.png")
                    img.save(f"{dirPath}/static/img/mediaImages/{movieId}_Cover.webp", "webp")
                    os.remove(f"{dirPath}/static/img/mediaImages/{movieId}_Cover.png")
                    movieCoverPath = f"/static/img/mediaImages/{movieId}_Cover.webp"
                except:
                    try:
                        os.rename(f"{dirPath}/static/img/mediaImages/{movieId}_Cover.png", f"{dirPath}/static/img/mediaImages/{movieId}_Cover.webp")
                        movieCoverPath = "/static/img/broken.webp"
                    except:
                        os.remove(f"{dirPath}/static/img/mediaImages/{movieId}_Cover.webp")
                        os.rename(f"{dirPath}/static/img/mediaImages/{movieId}_Cover.png", f"{dirPath}/static/img/mediaImages/{movieId}_Cover.webp")
                        movieCoverPath = f"/static/img/mediaImages/{movieId}_Cover.webp"
                with open(f"{dirPath}/static/img/mediaImages/{movieId}_Banner.png", "wb") as f:
                    f.write(requests.get(banniere).content)
                if res.backdrop_path == None:
                    banniere = f"https://image.tmdb.org/t/p/original{details.backdrop_path}"
                    if banniere != "https://image.tmdb.org/t/p/originalNone":
                        with open(f"{dirPath}/static/img/mediaImages/{movieId}_Banner.png", "wb") as f:
                            f.write(requests.get(banniere).content)
                    else:
                        banniere = "/static/img/broken.webp"
                try:
                    img = Image.open(f"{dirPath}/static/img/mediaImages/{movieId}_Banner.png")
                    img.save(f"{dirPath}/static/img/mediaImages/{movieId}_Banner.webp", "webp")
                    os.remove(f"{dirPath}/static/img/mediaImages/{movieId}_Banner.png")
                    banniere = f"/static/img/mediaImages/{movieId}_Banner.webp"
                except:
                    banniere = "/static/img/brokenBanner.webp"

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
                    actorId = cast.id
                    actorImage = f"https://www.themoviedb.org/t/p/w600_and_h900_bestv2{cast.profile_path}"
                    if not os.path.exists(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.webp"):
                        with open(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.png", "wb") as f:
                            f.write(requests.get(actorImage).content)
                        try:
                            img = Image.open(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.png")
                            img = img.save(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.webp", "webp")
                            os.remove(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.png")
                        except Exception as e:
                            os.rename(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.png", f"{dirPath}/static/img/mediaImages/Actor_{actorId}.webp")

                    actorImage = f"/static/img/mediaImages/Actor_{actorId}.webp"
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
                video_path = f"{path}\{start}{originalMovieTitle}"
                try:
                    length = length_video(video_path)
                    length = str(datetime.timedelta(seconds=length))
                    length = length.split(":")
                except Exception as e:
                    length = []

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
                slug = f"{start}{originalMovieTitle}"
                filmData = Movies(movieId, movieTitle, name, movieCoverPath, banniere, slug, description, note, date, json.dumps(movieGenre), str(duration), json.dumps(theCast), bandeAnnonceUrl, str(res["adult"]), libraryName=libraryName, alternativesNames=alternativesNames, vues=str({}))
                db.session.add(filmData)
                db.session.commit()
        elif searchedFilm.endswith("/") == False:
            allMoviesNotSorted.append(searchedFilm)

    movies = Movies.query.filter_by(libraryName=libraryName).all()
    moviesPath = os.listdir(path)
    for movie in movies:
        slug = movie.slug
        #print(f"Movie {movie.realTitle} slug: {slug}\n")
        possibleDirSlug = slug.split("/")[0:-1]
        possibleDirSlug = "/".join(possibleDirSlug)
        if slug not in moviesPath and possibleDirSlug == "":
            db.session.delete(movie)
            db.session.commit()
        elif slug not in moviesPath and possibleDirSlug != "":
            path = f"{path}\{possibleDirSlug}\{slug}"
            dirPath = f"{path}\{possibleDirSlug}"
            exist = os.path.exists(path)
            existDir = os.path.exists(dirPath)
            if not exist or not existDir:
                db.session.delete(movie)
                db.session.commit()

class EpisodeGroup():
    def __init__(self, **entries):
        if "success" in entries and entries["success"] is False:
            raise TMDbException(entries["status_message"])
        for key, value in entries.items():
            if isinstance(value, list):
                value = [EpisodeGroup(**item) if isinstance(item, dict) else item for item in value]
            elif isinstance(value, dict):
                value = EpisodeGroup(**value)
            setattr(self, key, value)

def getEpisodeGroupe(apikey, serieId, language="EN"):
    details = show.details(serieId)
    seasonsInfo = details.seasons
    serieTitle = details.name
    url = f"https://api.themoviedb.org/3/tv/{serieId}/episode_groups?api_key={apikey}&language={language}"
    r = requests.get(url)
    data = r.json()
    if data["results"]:
        #print(f"Found {len(data['results'])} episode groups for {serieTitle}")
        for episodeGroup in data["results"]:
            index = data["results"].index(episodeGroup) + 1
            name = episodeGroup["name"]
            episodeCount = episodeGroup["episode_count"]
            description = episodeGroup["description"]
            #print(f"{index}: Found {episodeCount} episodes for {name} ({description})")
        #print("0: Use the default episode group")
        selectedEpisodeGroup = int(input("Which episode group do you want to use ? "))
        if selectedEpisodeGroup > 0:
            theEpisodeGroup = data["results"]
            episode_group_data_url = f"https://api.themoviedb.org/3/tv/episode_group/{theEpisodeGroup['id']}?api_key={apikey}&language={language}"
            r = requests.get(episode_group_data_url)
            data = r.json()

            seasons = data["groups"]
            for season in seasons:
                seasonId = season["id"]
                seasonName = season["name"]
                episodesNumber = len(season["episodes"])
                releaseDate = season["episodes"][0]["air_date"]
                seasonNumber = season["order"]
                seasonDescription = season.overview
                seasonPoster = "/static/img/broken.png"

                #get the season from seasonId
                seasonsInfo = [season for season in seasonsInfo if season.id == seasonId]
                if seasonsInfo:
                    seasonsInfo = EpisodeGroup(id=seasonId, name=seasonName, episode_count=episodesNumber, air_date=releaseDate, season_number=seasonNumber, overview=seasonDescription, poster_path=seasonPoster)
        else:
            seasonsInfo = seasonsInfo

def getSeries(libraryName):
    allSeriesPath = Libraries.query.filter_by(libName=libraryName).first().libFolder
    try:
        allSeries = [name for name in os.listdir(allSeriesPath) if os.path.isdir(os.path.join(allSeriesPath, name)) and name.endswith((".rar", ".zip", ".part")) == False]
    except:
        return
    allSeasonsAppelations = ["S"]
    allEpisodesAppelations = ["E"]
    allSeriesDictTemp = {}
    for series in allSeries:
        uglySeasonAppelations = ["Saison", "Season", series.replace(" ", ".")]
        seasons = os.listdir(os.path.join(allSeriesPath, series))
        serieSeasons = {}
        for season in seasons:
            path = os.path.join(allSeriesPath, series)
            if (not (season.startswith(tuple(allSeasonsAppelations)) and season.endswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9"))) or season.startswith(tuple(uglySeasonAppelations))):
                allSeasons = os.listdir(f"{path}")
                for allSeason in allSeasons:
                    if ((allSeason.startswith(tuple(allSeasonsAppelations)) == False and allSeason.endswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")) == False) or season.startswith(tuple(uglySeasonAppelations))):
                        if os.path.isdir(f"{path}/{allSeason}") and not (allSeason.startswith(tuple(allSeasonsAppelations)) and allSeason.endswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9"))):
                            #print(f"For {uglySeasonAppelations[2]} : {allSeason}")
                            reponse = ask(f"I found that folder, can I rename it from {allSeason} to S{allSeasons.index(allSeason)+1}", AskResult.YES)
                            if reponse:
                                try:
                                    os.rename(f"{path}/{allSeason}", f"{path}/S{allSeasons.index(allSeason)+1}")
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



                        seasonEpisodes[oldIndex + 1] = f"{path}/{season}/{episode}"
                serieSeasons[seasonNumber] = seasonEpisodes
        serieData = {}
        serieData["seasons"] = serieSeasons
        allSeriesDictTemp[series] = serieData
    allSeriesName = []
    alreadyAddedSeries = []
    allSeries = allSeriesDictTemp
    for series in allSeries:
        allSeriesName.append(series)
    
    for serie in allSeriesName:
        if not isinstance(serie, str):
            #print(f"Error : {serie} is not a string")
            continue
        index = allSeriesName.index(serie) + 1
        percentage = index * 100 / len(allSeriesName)

        loadingFirstPart = ("•" * int(percentage * 0.2))[:-1]
        loadingFirstPart = f"{loadingFirstPart}➤"
        loadingSecondPart = "•" * (20 - int(percentage * 0.2))
        loading = f"{str(int(percentage)).rjust(3)}% | [\33[32m{loadingFirstPart} \33[31m{loadingSecondPart}\33[0m] | {serie} | {index}/{len(allSeriesName)}                              "
        print("\033[?25l", end="")
        print(loading, end="\r", flush=True)
        show = TV()
        serieTitle = serie
        originalSerieTitle = serieTitle
        try:
            serieModifiedTime = os.path.getmtime(f"{allSeriesPath}/{originalSerieTitle}")
        except FileNotFoundError:
            print(f"Cant find {originalSerieTitle}")
            continue
        try:
            search = show.search(serieTitle)
        except TMDbException as e:
            allSeriesNotSorted.append(serieTitle)
            break

        if not search:
            allSeriesNotSorted.append(serieTitle)
            continue

        askForGoodSerie = config["ChocolateSettings"]["askWhichSerie"]
        bestMatch = search[0]
        if askForGoodSerie == "false" or len(search)==1:
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

        res = bestMatch
        serieId = res.id

        if (db.session.query(Series).filter_by(originalName=serieTitle).first() is not None):
            serieId = db.session.query(Series).filter_by(originalName=serieTitle).first().id
        exists = db.session.query(Series).filter_by(id=serieId).first() is not None
        details = show.details(serieId)
        seasonsInfo = details.seasons
        alreadyAddedSeries.append(serieId)
        if not exists:
            name = res.name
            serieCoverPath = f"https://image.tmdb.org/t/p/original{res.poster_path}"
            banniere = f"https://image.tmdb.org/t/p/original{res.backdrop_path}"
            if not os.path.exists(f"{dirPath}/static/img/mediaImages/{serieId}_Cover.png"):
                with open(f"{dirPath}/static/img/mediaImages/{serieId}_Cover.png","wb") as f:
                    f.write(requests.get(serieCoverPath).content)
                try:
                    img = Image.open(f"{dirPath}/static/img/mediaImages/{serieId}_Cover.png")
                    img = img.save(f"{dirPath}/static/img/mediaImages/{serieId}_Cover.webp", "webp")
                    os.remove(f"{dirPath}/static/img/mediaImages/{serieId}_Cover.png")
                except Exception as e:
                    print(e)
                    pass

            if not os.path.exists(f"{dirPath}/static/img/mediaImages/{serieId}_Banner.png"):
                with open(f"{dirPath}/static/img/mediaImages/{serieId}_Banner.png","wb") as f:
                    f.write(requests.get(banniere).content)
                try:
                    img = Image.open(f"{dirPath}/static/img/mediaImages/{serieId}_Banner.png")
                    img = img.save(f"{dirPath}/static/img/mediaImages/{serieId}_Banner.webp", "webp")
                    os.remove(f"{dirPath}/static/img/mediaImages/{serieId}_Banner.png")
                except Exception as e:
                    print(e)
                    pass

            banniere = f"/static/img/mediaImages/{serieId}_Banner.webp"
            serieCoverPath = f"/static/img/mediaImages/{serieId}_Cover.webp"
            description = res["overview"]
            note = res.vote_average
            date = res.first_air_date
            cast = details.credits.cast
            runTime = details.episode_run_time
            duration = ""
            for i in range(len(runTime)):
                if i != len(runTime) - 1:
                    duration += f"{str(runTime[i])}:"
                else:
                    duration += f"{str(runTime[i])}"
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
                actorName = actor.name.replace("/", "")
                actorId = actor.id
                actorImage = f"https://image.tmdb.org/t/p/original{actor.profile_path}"
                if not os.path.exists(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.webp"):
                    with open(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.png", "wb") as f:
                        f.write(requests.get(actorImage).content)
                    img = Image.open(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.png")
                    img = img.save(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.webp", "webp")
                    os.remove(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.png")

                actorImage = f"/static/img/mediaImages/Actor_{actorId}.webp"
                actorCharacter = actor.character
                actor.profile_path = str(actorImage)
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
            if os.path.isdir(f"{allSeriesPath}/{originalSerieTitle}/{season}"):
                season = re.sub(r"\D", "", season)
                seasonsNumber.append(int(season))
        
        seasons = Seasons.query.filter_by(serie=serieId).all()
        seasonInDb = [season for season in seasons]
        for season in seasonsInfo:
            url = f"{allSeriesPath}/{originalSerieTitle}/S{season.season_number}"
            if not os.path.exists(url):
                continue
            seasonInDB = Seasons.query.filter_by(seasonId=season.id).first()
            if seasonInDB:
                modifiedDate = seasonInDB.modifiedDate
                actualSeasonModifiedTime = os.path.getmtime(url)
            if seasonInDB is None or modifiedDate != actualSeasonModifiedTime:
                #print(f"Modified time of {originalSerieTitle} S{season.season_number} is different from the one in the database, updating...")
                try:
                    allEpisodes = [ f for f in os.listdir(f"{allSeriesPath}/{serie}/S{season.season_number}") if os.path.isfile(os.path.join(f"{allSeriesPath}/{serie}/S{season.season_number}", f)) ]
                except FileNotFoundError as e:
                    continue
                if len(allEpisodes) > 0:
                    releaseDate = season.air_date
                    episodesNumber = season.episode_count
                    seasonNumber = season.season_number
                    seasonId = season.id
                    seasonName = season.name
                    seasonDescription = season.overview
                    seasonPoster = season.poster_path
                    
                    try:
                        exists = Seasons.query.filter_by(seasonId=seasonId).first() is not None
                    except sqlalchemy.exc.PendingRollbackError as e:
                        db.session.rollback()
                        exists = Seasons.query.filter_by(seasonId=seasonId).first() is not None
                    #number of episodes in the season
                    try:
                        seasonModifiedTime = os.path.getmtime(f"{allSeriesPath}/{serie}/S{seasonNumber}")
                        savedModifiedTime = Seasons.query.filter_by(seasonId=seasonId).first().seasonModifiedTime
                    except AttributeError as e:
                        seasonModifiedTime = os.path.getmtime(f"{allSeriesPath}/{serie}/S{seasonNumber}")
                        savedModifiedTime = 0
                    if not exists or (seasonModifiedTime != savedModifiedTime):
                        seasonCoverPath = (f"https://image.tmdb.org/t/p/original{seasonPoster}")
                        if not os.path.exists(f"{dirPath}/static/img/mediaImages/{seasonId}_Cover.png"):
                            with open(f"{dirPath}/static/img/mediaImages/{seasonId}_Cover.png", "wb") as f:
                                f.write(requests.get(seasonCoverPath).content)
                            try:
                                img = Image.open(f"{dirPath}/static/img/mediaImages/{seasonId}_Cover.png")
                                img = img.save(f"{dirPath}/static/img/mediaImages/{seasonId}_Cover.webp", "webp")
                                os.remove(f"{dirPath}/static/img/mediaImages/{seasonId}_Cover.png")
                                seasonCoverPath = f"/static/img/mediaImages/{seasonId}_Cover.webp"
                            except:
                                with open(f"{dirPath}/static/img/mediaImages/{seasonId}_Cover.png", "wb") as f:
                                    f.write(requests.get(seasonCoverPath).content)
                                try:
                                    img = Image.open(f"{dirPath}/static/img/mediaImages/{seasonId}_Cover.png")
                                    img = img.save(f"{dirPath}/static/img/mediaImages/{seasonId}_Cover.webp", "webp")
                                    os.remove(f"{dirPath}/static/img/mediaImages/{seasonId}_Cover.png")
                                    seasonCoverPath = f"/static/img/mediaImages/{seasonId}_Cover.webp"
                                except:
                                    seasonCoverPath = f"/static/img/brokenImage.png"


                        allSeasonsUglyDict = os.listdir(f"{allSeriesPath}/{serie}")
                        try:
                            allSeasons = [int(season.replace("S", "")) for season in allSeasonsUglyDict if os.path.isdir(f"{allSeriesPath}/{serie}/{season}")]
                        except ValueError as e:
                            print(f"Error with {serie}:\n{e}")
                        
                        try:
                            modifiedDate = os.path.getmtime(f"{allSeriesPath}/{serie}/S{seasonNumber}")
                        except FileNotFoundError as e:
                            modifiedDate = 0

                        allEpisodesInDB = Episodes.query.filter_by(seasonId=seasonId).all()
                        allEpisodesInDB = [episode.episodeName for episode in allEpisodesInDB]

                        exists = Seasons.query.filter_by(seasonId=seasonId).first() is not None
                        if not exists:
                            thisSeason = Seasons(serie=serieId, release=releaseDate, episodesNumber=episodesNumber, seasonNumber=seasonNumber, seasonId=seasonId, seasonName=seasonName, seasonDescription=seasonDescription, seasonCoverPath=seasonCoverPath, modifiedDate=modifiedDate, numberOfEpisodeInFolder=len(allEpisodes))
                            
                            try:
                                db.session.add(thisSeason)
                                db.session.commit()
                            except sqlalchemy.exc.PendingRollbackError as e:
                                db.session.rollback()
                                db.session.add(thisSeason)
                                db.session.commit()
                        if len(allEpisodes) != len(allEpisodesInDB):
                            for episode in allEpisodes:
                                slug = f"/{serie}/S{seasonNumber}/{episode}"
                                episodeName = slug.split("/")[-1]
                                episodeName, extension = os.path.splitext(episodeName)
                                try:
                                    episodeIndex = int(episodeName.replace("E", ""))
                                except Exception as e:
                                    continue
                                try:
                                    try:
                                        exists = Episodes.query.filter_by(episodeNumber=episodeIndex, seasonId=seasonId).first() is not None
                                    except sqlalchemy.exc.PendingRollbackError as e:
                                        db.session.rollback()
                                        exists = Episodes.query.filter_by(episodeNumber=episodeIndex, seasonId=seasonId).first() is not None
                                    if not exists:
                                        showEpisode = Episode()
                                        episodeDetails = showEpisode.details(serieId, seasonNumber, episodeIndex)
                                        realEpisodeName = episodeDetails.name
                                        episodeInfo = showEpisode.details(serieId, seasonNumber, episodeIndex)
                                        episodeId = episodeInfo.id
                                        coverEpisode = f"https://image.tmdb.org/t/p/original{episodeInfo.still_path}"
                                        
                                        if not os.path.exists(f"{dirPath}/static/img/mediaImages/{seasonId}_{episodeId}_Cover.webp"):
                                            with open(f"{dirPath}/static/img/mediaImages/{seasonId}_{episodeId}_Cover.png","wb") as f:
                                                f.write(requests.get(coverEpisode).content)                                        
                                            try:
                                                img = Image.open(f"{dirPath}/static/img/mediaImages/{seasonId}_{episodeId}_Cover.png")
                                                img = img.save(f"{dirPath}/static/img/mediaImages/{seasonId}_{episodeId}_Cover.webp", "webp")
                                                os.remove(f"{dirPath}/static/img/mediaImages/{seasonId}_{episodeId}_Cover.png")
                                                coverEpisode = f"/static/img/mediaImages/{seasonId}_{episodeId}_Cover.webp"
                                            except:
                                                coverEpisode = f"/static/img/mediaImages/{seasonId}_{episodeId}_Cover.png"
                                        try:
                                            exists = Episodes.query.filter_by(episodeId=episodeId).first() is not None
                                        except sqlalchemy.exc.PendingRollbackError as e:
                                            db.session.rollback()
                                            exists = Episodes.query.filter_by(episodeId=episodeId).first() is not None
                                        if not exists:
                                            episodeData = Episodes(episodeId=episodeId, episodeName=realEpisodeName, seasonId=seasonId, episodeNumber=episodeIndex, episodeDescription=episodeInfo.overview, episodeCoverPath=coverEpisode, releaseDate=episodeInfo.air_date, slug=slug, introStart=0.0, introEnd=0.0)
                                            thisSeason = Seasons.query.filter_by(seasonId=seasonId).first()
                                            thisSeason.numberOfEpisodeInFolder += 1
                                            try:
                                                db.session.add(episodeData)
                                                db.session.commit()
                                            except:
                                                db.session.rollback()
                                                db.session.add(episodeData)
                                                db.session.commit()
                                except TMDbException as e:
                                    print(f"I didn't find an the episode {episodeIndex} of the season {seasonNumber} of the serie with ID {serieId} :",e)
                        else:
                            pass

    allFiles = [name for name in os.listdir(allSeriesPath) if os.path.isfile(os.path.join(allSeriesPath, name)) and name.endswith((".rar", ".zip", ".part")) == False]

    for file in allFiles:
        slug = f"/{file}"
        exists = Episodes.query.filter_by(slug=slug).first() is not None
        if not exists:
            guess = guessit(file)
            title = guess["title"]
            season = guess["season"]
            seasonIndex = season
            episode = guess["episode"]
            episodeIndex = episode
            originalName = title
            series = TV()
            show = series.search(title)
            res = show[0]
            serieId = res.id
            details = series.details(serieId)
            seasonId = details.seasons[season-1].id
            for seasonTMDB in details.seasons:
                if str(seasonTMDB.season_number) == str(season):
                    seasonId = seasonTMDB.id
                    seasonApi = seasonTMDB
                    break
            
            serieExists = Series.query.filter_by(id=serieId).first() is not None
            if not serieExists:
                name = res.name
                serieCoverPath = f"https://image.tmdb.org/t/p/original{res.poster_path}"
                banniere = f"https://image.tmdb.org/t/p/original{res.backdrop_path}"
                if not os.path.exists(f"{dirPath}/static/img/mediaImages/{serieId}_Cover.png"):
                    with open(f"{dirPath}/static/img/mediaImages/{serieId}_Cover.png","wb") as f:
                        f.write(requests.get(serieCoverPath).content)
                    try:
                        img = Image.open(f"{dirPath}/static/img/mediaImages/{serieId}_Cover.png")
                        img = img.save(f"{dirPath}/static/img/mediaImages/{serieId}_Cover.webp", "webp")
                        os.remove(f"{dirPath}/static/img/mediaImages/{serieId}_Cover.png")
                    except Exception as e:
                        print(e)
                        pass

                if not os.path.exists(f"{dirPath}/static/img/mediaImages/{serieId}_Banner.png"):
                    with open(f"{dirPath}/static/img/mediaImages/{serieId}_Banner.png","wb") as f:
                        f.write(requests.get(banniere).content)
                    try:
                        img = Image.open(f"{dirPath}/static/img/mediaImages/{serieId}_Banner.png")
                        img = img.save(f"{dirPath}/static/img/mediaImages/{serieId}_Banner.webp", "webp")
                        os.remove(f"{dirPath}/static/img/mediaImages/{serieId}_Banner.png")
                    except Exception as e:
                        print(e)
                        pass

                banniere = f"/static/img/mediaImages/{serieId}_Banner.webp"
                serieCoverPath = f"/static/img/mediaImages/{serieId}_Cover.webp"
                description = res["overview"]
                note = res.vote_average
                date = res.first_air_date
                cast = details.credits.cast
                runTime = details.episode_run_time
                duration = ""
                for i in range(len(runTime)):
                    if i != len(runTime) - 1:
                        duration += f"{str(runTime[i])}:"
                    else:
                        duration += f"{str(runTime[i])}"
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
                    actorName = actor.name.replace("/", "")
                    actorId = actor.id
                    actorImage = f"https://image.tmdb.org/t/p/original{actor.profile_path}"
                    if not os.path.exists(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.webp"):
                        with open(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.png", "wb") as f:
                            f.write(requests.get(actorImage).content)
                        img = Image.open(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.png")
                        img = img.save(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.webp", "webp")
                        os.remove(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.png")

                    actorImage = f"/static/img/mediaImages/Actor_{actorId}.webp"
                    actorCharacter = actor.character
                    actor.profile_path = str(actorImage)
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

            seasonExists = Seasons.query.filter_by(serie=serieId, seasonId=seasonId).first() is not None
            season = seasonApi
            if not seasonExists:
                releaseDate = season.air_date
                episodesNumber = season.episode_count
                seasonNumber = season.season_number
                seasonName = season.name
                seasonDescription = season.overview
                seasonPoster = season.poster_path

                try:
                    seasonModifiedTime = os.path.getmtime(f"{allSeriesPath}/{serie}/S{seasonNumber}")
                    savedModifiedTime = Seasons.query.filter_by(seasonId=seasonId).first().seasonModifiedTime
                except AttributeError as e:
                    seasonModifiedTime = os.path.getmtime(f"{allSeriesPath}/{serie}/S{seasonNumber}")
                    savedModifiedTime = 0

                seasonCoverPath = (f"https://image.tmdb.org/t/p/original{seasonPoster}")
                if not os.path.exists(f"{dirPath}/static/img/mediaImages/{seasonId}_Cover.png"):
                    with open(f"{dirPath}/static/img/mediaImages/{seasonId}_Cover.png", "wb") as f:
                        f.write(requests.get(seasonCoverPath).content)
                    try:
                        img = Image.open(f"{dirPath}/static/img/mediaImages/{seasonId}_Cover.png")
                        img = img.save(f"{dirPath}/static/img/mediaImages/{seasonId}_Cover.webp", "webp")
                        os.remove(f"{dirPath}/static/img/mediaImages/{seasonId}_Cover.png")
                        seasonCoverPath = f"/static/img/mediaImages/{seasonId}_Cover.webp"
                    except:
                        with open(f"{dirPath}/static/img/mediaImages/{seasonId}_Cover.png", "wb") as f:
                            f.write(requests.get(seasonCoverPath).content)
                        try:
                            img = Image.open(f"{dirPath}/static/img/mediaImages/{seasonId}_Cover.png")
                            img = img.save(f"{dirPath}/static/img/mediaImages/{seasonId}_Cover.webp", "webp")
                            os.remove(f"{dirPath}/static/img/mediaImages/{seasonId}_Cover.png")
                            seasonCoverPath = f"/static/img/mediaImages/{seasonId}_Cover.webp"
                        except:
                            seasonCoverPath = f"/static/img/brokenImage.png"
                
                try:
                    modifiedDate = os.path.getmtime(f"{allSeriesPath}/{serie}/S{seasonNumber}")
                except FileNotFoundError as e:
                    modifiedDate = 0
                
                seasonObject = Seasons(serie=serieId, seasonId=seasonId, seasonName=seasonName, seasonDescription=seasonDescription, seasonCoverPath=seasonCoverPath, seasonNumber=seasonNumber, episodesNumber=episodesNumber, release=releaseDate, modifiedDate=modifiedDate, numberOfEpisodeInFolder=0)

                db.session.add(seasonObject)
                db.session.commit()


            showEpisode = Episode()
            seasonNumber = seasonIndex
            serieId, seasonNumber, episodeIndex = str(serieId), str(seasonNumber), str(episodeIndex)
            episodeInfo = showEpisode.details(serieId, seasonIndex, episodeIndex)
            try:
                exists = Episodes.query.filter_by(episodeNumber=episodeIndex, seasonId=seasonId).first() is not None
            except sqlalchemy.exc.PendingRollbackError as e:
                db.session.rollback()
                exists = Episodes.query.filter_by(episodeNumber=episodeIndex, seasonId=seasonId).first() is not None
            if not exists:
                showEpisode = Episode()
                episodeInfo = showEpisode.details(serieId, seasonNumber, episodeIndex)
                realEpisodeName = episodeInfo.name
                episodeId = episodeInfo.id
                coverEpisode = f"https://image.tmdb.org/t/p/original{episodeInfo.still_path}"
                
                if not os.path.exists(f"{dirPath}/static/img/mediaImages/{seasonId}_{episodeId}_Cover.webp"):
                    with open(f"{dirPath}/static/img/mediaImages/{seasonId}_{episodeId}_Cover.png","wb") as f:
                        f.write(requests.get(coverEpisode).content)                                        
                    try:
                        img = Image.open(f"{dirPath}/static/img/mediaImages/{seasonId}_{episodeId}_Cover.png")
                        img = img.save(f"{dirPath}/static/img/mediaImages/{seasonId}_{episodeId}_Cover.webp", "webp")
                        os.remove(f"{dirPath}/static/img/mediaImages/{seasonId}_{episodeId}_Cover.png")
                        coverEpisode = f"/static/img/mediaImages/{seasonId}_{episodeId}_Cover.webp"
                    except:
                        coverEpisode = f"/static/img/mediaImages/{seasonId}_{episodeId}_Cover.png"
                try:
                    exists = Episodes.query.filter_by(episodeId=episodeId).first() is not None
                except sqlalchemy.exc.PendingRollbackError as e:
                    db.session.rollback()
                    exists = Episodes.query.filter_by(episodeId=episodeId).first() is not None
                if not exists:
                    episodeData = Episodes(episodeId=episodeId, episodeName=realEpisodeName, seasonId=seasonId, episodeNumber=episodeIndex, episodeDescription=episodeInfo.overview, episodeCoverPath=coverEpisode, releaseDate=episodeInfo.air_date, slug=slug, introStart=0.0, introEnd=0.0)
                    thisSeason = Seasons.query.filter_by(seasonId=seasonId).first()
                    thisSeason.numberOfEpisodeInFolder += 1
                    try:
                        db.session.add(episodeData)
                        db.session.commit()
                    except:
                        db.session.rollback()
                        db.session.add(episodeData)
                        db.session.commit()


    allSeriesInDB = Series.query.all()
    allSeriesInDB = [serie.originalName for serie in allSeriesInDB if serie.libraryName == libraryName]
    
    for serie in allSeriesInDB:
        if serie not in allSeries:
            serieId = Series.query.filter_by(originalName=serie).first().id
            allSeasons = Seasons.query.filter_by(serie=serieId).all()
            for season in allSeasons:
                seasonId = season.seasonId
                allEpisodes = Episodes.query.filter_by(seasonId=seasonId).all()
                for episode in allEpisodes:
                    try:
                        db.session.delete(episode)
                        db.session.commit()
                    except:
                        db.session.rollback()
                        db.session.delete(episode)
                        db.session.commit()
                try:
                    db.session.delete(season)
                    db.session.commit()
                except:
                    db.session.rollback()
                    db.session.delete(season)
                    db.session.commit()
            try:
                db.session.delete(Series.query.filter_by(id=serieId).first())
                db.session.commit()
            except:
                db.session.rollback()
                db.session.delete(Series.query.filter_by(id=serieId).first())
                db.session.commit()

def getGames(libraryName):
    allGamesPath = Libraries.query.filter_by(libName=libraryName).first().libFolder
    try:
        allConsoles = [name for name in os.listdir(allGamesPath) if os.path.isdir(os.path.join(allGamesPath, name)) and name.endswith((".rar", ".zip", ".part")) == False]
    except:
        return
    
    for console in allConsoles:
        if os.listdir(f"{allGamesPath}/{console}") == []:
            allConsoles.remove(console)
    saidPS1 = False
    supportedConsoles = ['3DO', 'Amiga', 'Atari 2600', 'Atari 5200', 'Atari 7800', 'Atari Jaguar', 'Atari Lynx', 'GB', 'GBA', 'GBC', 'N64', 'NDS', 'NES', 'SNES', 'Neo Geo Pocket', 'PSX', 'Sega 32X', 'Sega CD', 'Sega Game Gear', 'Sega Master System', 'Sega Mega Drive', 'Sega Saturn', "PS1"]
    supportedFileTypes = [".zip", ".adf", ".adz", ".dms", ".fdi", ".ipf", ".hdf", ".lha", ".slave", ".info", ".cdd", ".nrg", ".mds", ".chd", ".uae", ".m3u", ".a26", ".a52", ".a78", ".j64", ".lnx", ".gb", ".gba", ".gbc", ".n64", ".nds", ".nes", ".ngp", ".psx", ".sfc", ".smc", ".smd", ".32x", ".cd", ".gg", ".md", ".sat", ".sms"]
    for console in allConsoles:
        if console not in supportedConsoles:
            print(f"{console} is not supported or the console name is not correct, here is the list of supported consoles: \n{', '.join(supportedConsoles)} rename the folder to one of these names if it's the correct console")
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
        allFiles = os.listdir(f"{allGamesPath}/{console}")
        for file in allFiles:
            #get all games in the db
            allGamesInDB = Games.query.all()
            allGamesInDB = [game.slug for game in allGamesInDB if game.libraryName == libraryName]
            numberOfGamesInDB = len(allGamesInDB)
            numberOfGamesInFolder = len(allFiles)
            if numberOfGamesInDB < numberOfGamesInFolder:
                exists = Games.query.filter_by(slug=f"{allGamesPath}/{console}/{file}").first() is not None
                if file.endswith(tuple(supportedFileTypes)) and exists == False:
                    
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
        gamesInDb = Games.query.filter_by(console=console).all()
        gamesInDb = [ game.realTitle for game in gamesInDb ]
        for game in gamesInDb:
            if game not in allFiles:
                game = Games.query.filter_by(console=console, realTitle=game).first()
                db.session.delete(game)
                db.session.commit()
            
def getOthersVideos(library):    
    allVideosPath = Libraries.query.filter_by(libName=library).first().libFolder
    try:
        allVideos = os.listdir(allVideosPath)
    except:
        return
    supportedVideoTypes = [".mp4", ".webm", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".mpg", ".mpeg"]

    allVideos = [ video for video in allVideos if os.path.splitext(video)[1] in supportedVideoTypes ]

    for video in allVideos:
        title, extension = os.path.splitext(video)

        index = allVideos.index(video) + 1
        percentage = index * 100 / len(allVideos)

        loadingFirstPart = ("•" * int(percentage * 0.2))[:-1]
        loadingFirstPart = f"{loadingFirstPart}➤"
        loadingSecondPart = "•" * (20 - int(percentage * 0.2))
        loading = f"{str(int(percentage)).rjust(3)}% | [\33[32m{loadingFirstPart} \33[31m{loadingSecondPart}\33[0m] | {title} | {index}/{len(allVideos)}                                                      "
        print("\033[?25l", end="")
        print(loading, end="\r", flush=True)

        slug = f"{allVideosPath}/{video}"
        exists = OthersVideos.query.filter_by(slug=slug).first() is not None
        if not exists:

            with open(slug, "rb") as f:
                video_hash = zlib.crc32(f.read())

            # Conversion du hash en chaîne hexadécimale
            video_hash_hex = hex(video_hash)[2:]

            # Récupération des 10 premiers caractères
            videoHash = video_hash_hex[:10]
            videoDuration = length_video(slug)
            middle = videoDuration // 2
            banner = f"/static/img/mediaImages/Other_Banner_{library}_{videoHash}.webp"
            command = ["ffmpeg", "-i", slug, "-vf", f"select='eq(n,{middle})'", "-vframes", "1", f"{dir}{banner}", "-y"]
            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.getsize(f"{dir}{banner}") == 0:
                generateImage(title, library, f"{dir}{banner}")
            banner = f"static/img/mediaImages/Other_Banner_{library}_{videoHash}.webp"
            video = OthersVideos(videoHash=videoHash, title=title, slug=slug, banner=banner, duration=videoDuration, libraryName=library, vues=str({}))
            db.session.add(video)
            db.session.commit()
        
    for video in OthersVideos.query.filter_by(libraryName=library).all():
        path = video.slug
        if not os.path.exists(path):
            db.session.delete(video)
            db.session.commit()

def generateImage(title, librairie, banner):
    from PIL import Image, ImageDraw, ImageFont
    largeur = 1280
    hauteur = 720
    image = Image.new('RGB', (largeur, hauteur), color='#1d1d1d')
    
    # Ajouter les textes au centre de l'image
    draw = ImageDraw.Draw(image)
    
    # Charger la police Poppins
    font_path = f"{dir}/static/fonts/Poppins-Medium.ttf"
    font_title = ImageFont.truetype(font_path, size=70)
    font_librairie = ImageFont.truetype(font_path, size=50)
    
    # Positionner les textes au centre de l'image
    titre_larg, titre_haut = draw.textsize(title, font=font_title)
    librairie_larg, librairie_haut = draw.textsize(librairie, font=font_librairie)
    x_title = int((largeur - titre_larg) / 2)
    y_title = int((hauteur - titre_haut - librairie_haut - 50) / 2)
    x_librairie = int((largeur - librairie_larg) / 2)
    y_librairie = y_title + titre_haut + 50
    
    # Ajouter le texte du titre
    draw.text((x_title, y_title), title, font=font_title, fill='white', align='center')
    
    # Ajouter le texte de la librairie
    draw.text((x_librairie, y_librairie), librairie, font=font_librairie, fill='white', align='center')
    
    # Enregistrer l'image
    os.remove(banner)
    image.save(banner, 'webp')

def getBooks(library):
    allBooks = Libraries.query.filter_by(libName=library)
    allBooksPath = allBooks.first().libFolder

    allBooks = [ book for book in os.listdir(allBooksPath) ]

    imageFunctions = {
        ".pdf": getPDFCover,
        ".epub": getEPUBCover,
        ".cbz": getCBZCover,
        ".cbr": getCBRCover,
    }

    for book in allBooks:
        name, extension = os.path.splitext(book)
        
        index = allBooks.index(book) + 1
        percentage = index * 100 / len(allBooks)

        loadingFirstPart = ("•" * int(percentage * 0.2))[:-1]
        loadingFirstPart = f"{loadingFirstPart}➤"
        loadingSecondPart = "•" * (20 - int(percentage * 0.2))
        loading = f"{str(int(percentage)).rjust(3)}% | [\33[32m{loadingFirstPart} \33[31m{loadingSecondPart}\33[0m] | {name} | {index}/{len(allBooks)}                                                      "
        print("\033[?25l", end="")
        print(loading, end="\r", flush=True)

        slug = f"{allBooksPath}/{book}"
        categoryName = book
        libName = library

        if os.path.isdir(slug):
            for bookInside in os.listdir(slug):
                exists = Books.query.filter_by(slug=f"{slug}/{bookInside}").first() is not None
                name, extension = os.path.splitext(bookInside)
                if extension in imageFunctions.keys() and not exists:
                    bookSlug = f"{slug}/{bookInside}"
                    bookCover, bookType = imageFunctions[extension](bookSlug, name)
                    library = f"{libName}-{categoryName}"
                    book = Books(title=name, slug=bookSlug, bookType=bookType, cover=bookCover, libraryName=library)
                    db.session.add(book)
                    db.session.commit()
                    bookId = book.id
                    name, extension = os.path.splitext(bookCover)
                    bookCover = f"\static\img\mediaImages\Books_Banner_{categoryName}_{bookId}{extension}"
                    try:
                        os.rename(f"{dirPath}{book.cover}", f"{dirPath}{bookCover}")
                    except:
                        pass
                    book.cover = bookCover
                    db.session.commit()
                #create a new book in the database for the category
            exists = Books.query.filter_by(slug=slug).first() is not None
            if not exists:
                #get the first book in the category
                firstBook = Books.query.filter_by(libraryName=f"{libName}-{categoryName}").first()
                original = firstBook.cover
                target = f"\static\img\mediaImages\Book_Category_{categoryName}.webp"
                #copy the cover of the first book with the category name
                import shutil
                shutil.copyfile(f"{dirPath}{original}", f"{dirPath}{target}")
                print(f"Génération de la couverture pour {slug} ({original} -> {target})")
                library = f"{libName}"
                book = Books(title=categoryName, slug=slug, bookType="folder", cover=bookCover, libraryName=library)
                db.session.add(book)
                db.session.commit()

        exists = Books.query.filter_by(slug=slug).first() is not None
        if not exists and not os.path.isdir(slug):
            if extension in imageFunctions.keys():
                print(f"Génération de la couverture pour {slug}")
                bookCover, bookType = imageFunctions[extension](slug, name)
                book = Books(title=name, slug=slug, bookType=bookType, cover=bookCover, libraryName=library)
                db.session.add(book)
                db.session.commit()
                bookId = book.id
                name, extension = os.path.splitext(bookCover)
                bookCover = f"\static\img\mediaImages\Books_Banner_{bookId}{extension}"
                os.rename(f"{dirPath}{book.cover}", f"{dirPath}{bookCover}")
                book.cover = bookCover
                db.session.commit()
    allBooksInDb = Books.query.filter_by(libraryName=library).all()
    for book in allBooksInDb:
        if not os.path.exists(book.slug):
            print(f"Suppression de {book.slug}")
            db.session.delete(book)
            db.session.commit()



def getPDFCover(path, name):
    import fitz
    pdfDoc = fitz.open(path)
    # Récupérez la page demandée
    page = pdfDoc[0]
    # Créez une image à partir de la page
    pix = page.get_pixmap()
    # Enregistre l'image
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    name = name.replace(" ", "_").replace("#", "")
    if os.path.exists(f"{dirPath}\static\img\mediaImages\Books_Banner_{name}.webp"):
        os.remove(f"{dirPath}\static\img\mediaImages\Books_Banner_{name}.webp")

    img.save(f"{dirPath}\static\img\mediaImages\Books_Banner_{name}.webp", "webp")
    path = f"\static\img\mediaImages\Books_Banner_{name}.webp"
    return path, "PDF"


def getEPUBCover(path, name):
    import fitz
    pdfDoc = fitz.open(path)
    # Récupérez la page demandée
    page = pdfDoc[0]
    # Créez une image à partir de la page
    pix = page.get_pixmap()
    # Enregistre l'image
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    name = name.replace(" ", "_").replace("#", "")
    if os.path.exists(f"{dirPath}\static\img\mediaImages\Books_Banner_{name}.webp"):
        os.remove(f"{dirPath}\static\img\mediaImages\Books_Banner_{name}.webp")

    img.save(f"{dirPath}\static\img\mediaImages\Books_Banner_{name}.webp", "webp")
    path = f"\static\img\mediaImages\Books_Banner_{name}.webp"

    return path, "EPUB"

def getCBZCover(path, name):
    name = name.replace(" ", "_").replace("#", "")
    try:
        with zipfile.ZipFile(path, "r") as zip_ref:
            # Parcourt tous les fichiers à l'intérieur du CBZ
            for file in zip_ref.filelist:
                # Vérifie si le fichier est une image
                if file.filename.endswith(".jpg") or file.filename.endswith(".png"):
                    # Ouvre le fichier image
                    with zip_ref.open(file) as image_file:
                        img = Image.open(io.BytesIO(image_file.read()))
                        # Enregistre l'image
                        img.save(f"{dirPath}\static\img\mediaImages\Books_Banner_{name}.webp", "webp")
                        break
                elif file.filename.endswith("/"):
                    with zip_ref.open(file) as image_file:
                        for file in zip_ref.filelist:
                            if file.filename.endswith(".jpg") or file.filename.endswith(".png"):
                                # Ouvre le fichier image
                                with zip_ref.open(file) as image_file:
                                    img = Image.open(io.BytesIO(image_file.read()))
                                    # Enregistre l'image
                                    img.save(f"{dirPath}\static\img\mediaImages\Books_Banner_{name}.webp", "webp")
                                    break
        return f"\static\img\mediaImages\Books_Banner_{name}.webp", "CBZ"
    except:
        return getCBRCover(path, name)
            

def getCBRCover(path, name):
    name = name.replace(" ", "_").replace("#", "")
    try:
        with rarfile.RarFile(path, "r") as rar_ref:
            # Parcourt tous les fichiers à l'intérieur du CBR
            for file in rar_ref.infolist():
                # Vérifie si le fichier est une image
                if file.filename.endswith(".jpg") or file.filename.endswith(".png"):
                    # Ouvre le fichier image
                    with rar_ref.open(file) as image_file:
                        img = Image.open(io.BytesIO(image_file.read()))
                        # Enregistre l'image
                        img.save(f"{dir}/static/img/mediaImages/Books_Banner_{name}.webp", "webp")
                        break
                elif file.filename.endswith("/"):
                    with rar_ref.open(file) as image_file:
                        img = Image.open(io.BytesIO(image_file.read()))
                        # Enregistre l'image
                        img.save(f"{dir}/static/img/mediaImages/Books_Banner_{name}.webp", "webp")
                        break
                                
            return f"\static\img\mediaImages\Books_Banner_{name}.webp", "CBR"
    except rarfile.NotRarFile:
        return getCBZCover(path, name)


@app.route("/checkLogin", methods=["POST"])
def checkLogin():
    global allAuthTokens
    token = request.get_json()["token"]
    if not token:
        return jsonify(False)
    
    token = "Bearer " + token
    
    if token not in allAuthTokens.keys():
        return jsonify(False)

    actualTime = time()
    tokenTime = allAuthTokens[token]["time"]
    ecart = actualTime - tokenTime
    if ecart > 3600:
        return jsonify(False)
    allAuthTokens[token]["time"] = time()
    return jsonify(True)
    
@app.route("/checkAccType", methods=["POST"])
def checkAccType():
    global allAuthTokens
    token = request.get_json()["token"]
    if not token:
        return jsonify("not logged")
    token = "Bearer " + token

    if token not in allAuthTokens.keys():
        return jsonify("not logged")
    
    username = allAuthTokens[token]["user"]
    user = Users.query.filter_by(name=username).first()
    if user:
        return jsonify(user.accountType)
    return jsonify("not logged")
    
@app.route("/checkDownload")
def checkDownload():
    config = configparser.ConfigParser()
    config.read("config.ini")
    if config["ChocolateSettings"]["allowdownload"] == "true":
        return jsonify(True)
    return jsonify(False)

def length_video(path: str) -> float:
    seconds = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path,
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
    language = config["ChocolateSettings"]["language"]
    #open language.json
    with open(f"{dirPath}/static/lang/languages.json", "r", encoding="utf-8") as f:
        languageDict = json.load(f)
    #if language not in languageDict use EN
    allLanguage = {}
    if language not in languageDict:
        allLanguage = languageDict["EN"]
    else:
        allLanguage = languageDict[language]
        
    g.language = allLanguage

    libraries = Libraries.query.all()
    libraries = [library.__dict__ for library in libraries]
    users = Users.query.all()
    for library in libraries:
        del library["_sa_instance_state"]

    libraries = sorted(libraries, key=lambda k: k['libName'])
    libraries = sorted(libraries, key=lambda k: k['libType'])
    
    g.libraries = libraries
    g.users = users
    g.languageCode = language

@app.route("/setTokenToActualTime/<token>")
def setTokenToActualTime(token):
    global allAuthTokens
    allAuthTokens[f"Bearer {token}"]["time"] -= 3600
    return jsonify(True)

@app.route("/service-worker.js")
def sw():
    return send_file(f"{dirPath}/static/js/service-worker.js", mimetype='application/javascript')

@app.route("/languageFile")
def languageFile():
    language = config["ChocolateSettings"]["language"]
    #open language.json
    with open(f"{dirPath}/static/lang/languages.json", "r", encoding="utf-8") as f:
        languageDict = json.load(f)
    #if language not in languageDict use EN
    allLanguage = languageDict[language] if language in languageDict else languageDict["EN"]
    return jsonify(allLanguage)

@app.route("/video/<movieId>.m3u8", methods=["GET"])
def create_m3u8(movieId):
    movie = Movies.query.filter_by(id=movieId).first()
    if not movie:
        abort(404)
    slug = movie.slug
    library = movie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    video_path = f"{path}/{slug}"
    duration = length_video(video_path)

    file = f"""#EXTM3U
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-TARGETDURATION:{CHUNK_LENGTH}\n\n"""

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""#EXTINF:{int(CHUNK_LENGTH)},\n/chunk/{movieId}-{(i // CHUNK_LENGTH) + 1}.ts\n"""

    file += """#EXT-X-ENDLIST"""

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{movieId}.m3u8"
    )

    return response

@app.route("/video/<quality>/<movieID>.m3u8", methods=["GET"])
def create_m3u8_quality(quality, movieID):
    movie = Movies.query.filter_by(id=movieID).first()
    slug = movie.slug
    library = movie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    video_path = f"{path}/{slug}"
    duration = length_video(video_path)
    file = f"""#EXTM3U
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-TARGETDURATION:{CHUNK_LENGTH}\n"""

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"#EXTINF:{int(CHUNK_LENGTH)},\n/chunk/{quality}/{movieID}-{(i // CHUNK_LENGTH) + 1}.ts\n"

    file += """#EXT-X-ENDLIST"""

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{movieID}.m3u8"
    )

    return response

@app.route("/other-video/<hash>", methods=["GET"])
def create_other_m3u8(hash):
    other = OthersVideos.query.filter_by(videoHash=hash).first()
    slug = other.slug
    library = other.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    video_path = slug
    duration = length_video(video_path)
    file = f"""
#EXTM3U

#EXT-X-VERSION:4
#EXT-X-TARGETDURATION:{CHUNK_LENGTH}
#EXT-X-MEDIA-SEQUENCE:1
    """

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""
#EXTINF:{float(CHUNK_LENGTH)},
/chunkOther/{hash}-{(i // CHUNK_LENGTH) + 1}.ts
        """

    file += """
#EXT-X-ENDLIST"""

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{hash}.m3u8"
    )

    return response

@app.route("/other-video/<quality>/<hash>", methods=["GET"])
def create_other_m3u8_quality(quality, hash):
    other = OthersVideos.query.filter_by(videoHash=hash).first()
    slug = other.slug
    library = other.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    video_path = slug
    duration = length_video(video_path)
    file = f"""
#EXTM3U

#EXT-X-VERSION:4
#EXT-X-TARGETDURATION:{CHUNK_LENGTH}
#EXT-X-MEDIA-SEQUENCE:1
    """

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""
#EXTINF:{float(CHUNK_LENGTH)},
/chunkOther/{quality}/{hash}-{(i // CHUNK_LENGTH) + 1}.ts
        """

    file += """
#EXT-X-ENDLIST"""

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{hash}.m3u8"
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
    episodePath = episodePath.replace("\\", "/")
    episodePath = f"{path}{episodePath}"
    duration = length_video(episodePath)
    file = f"""
#EXTM3U

#EXT-X-VERSION:4
#EXT-X-TARGETDURATION:{CHUNK_LENGTH}
#EXT-X-MEDIA-SEQUENCE:1
    """

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""
#EXTINF:{float(CHUNK_LENGTH)},
/chunkSerie/{episodeId}-{(i // CHUNK_LENGTH) + 1}.ts
        """

    file += """
#EXT-X-ENDLIST"""

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
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
    episodePath = episodePath.replace("\\", "/")
    episodePath = f"{path}{episodePath}"
    duration = length_video(episodePath)
    file = f"""
#EXTM3U

#EXT-X-VERSION:4
#EXT-X-TARGETDURATION:{CHUNK_LENGTH}
#EXT-X-MEDIA-SEQUENCE:1
    """

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""
#EXTINF:{float(CHUNK_LENGTH)},
/chunkSerie/{quality}/{episodeId}-{(i // CHUNK_LENGTH) + 1}.ts
        """

    file += """
#EXT-X-ENDLIST"""

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
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
    episodePath = episodePath.replace("\\", "/")
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
        "196k",
        "-ac",
        "2",
        "-f",
        "mpegts",
        "pipe:1",
    ]

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
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
    episodePath = episodePath.replace("\\", "/")
    episodePath = f"{path}{episodePath}"

    time_start = str(datetime.timedelta(seconds=seconds))
    time_end = str(datetime.timedelta(seconds=seconds + CHUNK_LENGTH))
    videoProperties = get_video_properties(episodePath)
    width = videoProperties["width"]
    height = videoProperties["height"]
    newWidth = int(float(quality))
    newHeight = round(float(width) / float(height) * newWidth)
    if (newHeight % 2) != 0:
        newHeight += 1
    logLevelValue = "error"


    bitrate = {
        "1080": "192k",
        "720": "192k",
        "480": "128k",
        "360": "128k",
        "240": "96k",
        "144": "64k",
    }

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
        bitrate[quality],
        "-ac",
        "2",
        "-f",
        "mpegts",
        "pipe:1",
    ]



    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{episodeId}-{idx}.ts"
    )

    return response


@app.route("/chunk/<movieID>-<int:idx>.ts", methods=["GET"])
def get_chunk(movieID, idx=0):
    seconds = (idx - 1) * CHUNK_LENGTH
    movie = Movies.query.filter_by(id=movieID).first()
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
        "196k",
        "-ac",
        "2",
        "-f",
        "mpegts",
        "pipe:1",
    ]
    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{movieID}-{idx}.ts"
    )

    return response

@app.route("/chunk/<quality>/<movieID>-<int:idx>.ts", methods=["GET"])
def get_chunk_quality(quality, movieID, idx=0):
    seconds = (idx - 1) * CHUNK_LENGTH

    movie = Movies.query.filter_by(id=movieID).first()
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
    newWidth = int(float(quality))
    newHeight = round(float(width) / float(height) * newWidth)
    while (newHeight % 8) != 0:
        newHeight += 1
    
    while (newWidth % 8) != 0:
        newWidth += 1


    aBitrate = {
        "1080": "192k",
        "720": "192k",
        "480": "128k",
        "360": "128k",
        "240": "96k",
        "144": "64k",
    }

    aBitrate = ((int(quality) - 144) / (1080 - 144)) * (192 - 64) + 64

    vBitrate = ((int(quality) - 144) / (1080 - 144)) * (5000 - 1500) + 1500

    if vBitrate < 1500:
        vBitrate = 1500


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
        f"{aBitrate}k",
        "-ac",
        "2",
        "-f",
        "mpegts",
        "pipe:1",
    ]

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{movieID}-{idx}.ts"
    )

    return response

@app.route("/chunkOther/<hash>-<int:idx>.ts", methods=["GET"])
def get_chunk_other(hash, idx=0):
    seconds = (idx - 1) * CHUNK_LENGTH
    movie = OthersVideos.query.filter_by(videoHash=hash).first()
    video_path = movie.slug

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
        "196k",
        "-ac",
        "2",
        "-f",
        "mpegts",
        "pipe:1",
    ]
    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{hash}-{idx}.ts"
    )

    return response

@app.route("/chunkOther/<quality>/<hash>-<int:idx>.ts", methods=["GET"])
def get_chunk_other_quality(quality, hash, idx=0):
    seconds = (idx - 1) * CHUNK_LENGTH
    movie = OthersVideos.query.filter_by(videoHash=hash).first()
    video_path = movie.slug

    time_start = str(datetime.timedelta(seconds=seconds))
    time_end = str(datetime.timedelta(seconds=seconds + CHUNK_LENGTH))
    videoProperties = get_video_properties(video_path)
    width = videoProperties["width"]
    height = videoProperties["height"]
    newWidth = int(float(quality))
    newHeight = round(float(width) / float(height) * newWidth)
    if (newHeight % 2) != 0:
        newHeight += 1

    bitrate = {
        "1080": "192k",
        "720": "192k",
        "480": "128k",
        "360": "128k",
        "240": "96k",
        "144": "64k",
    }

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
        bitrate[quality],
        "-ac",
        "2",
        "-f",
        "mpegts",
        "pipe:1",
    ]

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{hash}-{idx}.ts"
    )

    return response

@app.route("/chunkCaption/<subtitleType>/<index>/<movieID>.vtt", methods=["GET"])
def chunkCaption(movieID, subtitleType, index):
    subtitleType = subtitleType.lower()
    movie = Movies.query.filter_by(id=movieID).first()
    slug = movie.slug
    library = movie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    video_path = f"{path}/{slug}"
    if subtitleType == "srt":
        extractCaptionsCommand = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", video_path, "-map", f"0:{index}", "-f", "webvtt", "pipe:1",
        ]
        extractCaptions = subprocess.run(extractCaptionsCommand, stdout=subprocess.PIPE)

        extractCaptionsResponse = make_response(extractCaptions.stdout)
        extractCaptionsResponse.headers.set("Content-Type", "text/VTT")
        extractCaptionsResponse.headers.set(
            "Content-Disposition", "attachment", filename=f"{subtitleType}/{index}/{movieID}.vtt"
        )

        return extractCaptionsResponse
    return "Not supported"
        
            

@app.route("/getSettings", methods=["GET"])
def getSettings():
    allUsers = Users.query.all()
    allLibraries = Libraries.query.all()
    users = []
    for user in allUsers:
        user = user.__dict__
        del user["_sa_instance_state"]
        user["password"] = "Ratio"
        users.append(user)

    libs = []
    for library in allLibraries:
        library = library.__dict__
        del library["_sa_instance_state"]
        libs.append(library)
    
    data = {
        "users": users,
        "libraries": libs,
    }

    #read the config.ini file and get the settings
    config = configparser.ConfigParser()
    config.read("config.ini")
    allSections = config.sections()
    for section in allSections:
        sectionData = config[section]
        theData = {}
        for key in sectionData:
            theData[key] = sectionData[key]
        data[section] = theData
    
    return jsonify(data)

@app.route("/lookup", methods=["POST"])
def lookup():
    jsonFile = request.get_json()
    mediaType = jsonFile["mediaType"]
    query = jsonFile["query"]

    if mediaType == "movie":
        radarrAPIKey = config["APIKeys"]["radarr"]
        radarrURL = config["ARRSettings"]["radarrurl"]
        radarr = RadarrAPI(radarrURL, radarrAPIKey)
        searchResults = radarr.lookup_movie(query)
        return jsonify(searchResults)
    elif mediaType == "serie":
        sonarrAPIKey = config["APIKeys"]["sonarr"]
        sonarrURL = config["ARRSettings"]["sonarrurl"]
        sonarr = SonarrAPI(sonarrURL, sonarrAPIKey)
        searchResults = sonarr.lookup_series(query)
        return jsonify(searchResults)
    elif mediaType == "music":
        lidarrAPIKey = config["APIKeys"]["lidarr"]
        lidarrURL = config["ARRSettings"]["lidarrurl"]
        lidarr = LidarrAPI(lidarrURL, lidarrAPIKey)
        searchResults = lidarr.lookup(query)
        return jsonify(searchResults)
    elif mediaType == "book":
        readarrAPIKey = config["APIKeys"]["readarr"]
        readarrURL = config["ARRSettings"]["readarrurl"]
        readarr = ReadarrAPI(readarrURL, readarrAPIKey)
        searchResults = readarr.lookup_book(term=query)
        return jsonify(searchResults)

@app.route("/listQualities/<mediaType>", methods=["GET"])
def listQualities(mediaType):
    if mediaType == "movie":
        radarrAPIKey = config["APIKeys"]["radarr"]
        radarrURL = config["ARRSettings"]["radarrurl"]
        radarr = RadarrAPI(radarrURL, radarrAPIKey)
        qualityList = radarr.get_quality_profile()

        realQualityList = []

        for quality in qualityList:
            realQualityList.append({"id": quality["id"], "name": quality["name"]})

        #order the list by name
        realQualityList = sorted(realQualityList, key=lambda k: k['name'])

        return jsonify(realQualityList)
    elif mediaType == "serie":
        sonarrAPIKey = config["APIKeys"]["sonarr"]
        sonarrURL = config["ARRSettings"]["sonarrurl"]
        sonarr = SonarrAPI(sonarrURL, sonarrAPIKey)
        qualityList = sonarr.get_quality_profile()

        realQualityList = []

        for quality in qualityList:
            realQualityList.append({"id": quality["id"], "name": quality["name"]})

        #order the list by name
        realQualityList = sorted(realQualityList, key=lambda k: k['name'])

        return jsonify(realQualityList)

    elif mediaType == "music":
        lidarrAPIKey = config["APIKeys"]["lidarr"]
        lidarrURL = config["ARRSettings"]["lidarrurl"]
        lidarr = LidarrAPI(lidarrURL, lidarrAPIKey)
        qualityList = lidarr.get_quality_profile()

        realQualityList = []

        for quality in qualityList:
            realQualityList.append({"id": quality["id"], "name": quality["name"]})

        #order the list by name
        realQualityList = sorted(realQualityList, key=lambda k: k['name'])

        return jsonify(realQualityList)

    elif mediaType == "book":
        readarrAPIKey = config["APIKeys"]["readarr"]
        readarrURL = config["ARRSettings"]["readarrurl"]
        readarr = ReadarrAPI(readarrURL, readarrAPIKey)
        qualityList = readarr.get_quality_profile()

        realQualityList = []

        for quality in qualityList:
            realQualityList.append({"id": quality["id"], "name": quality["name"]})

        #order the list by name
        realQualityList = sorted(realQualityList, key=lambda k: k['name'])

        return jsonify(realQualityList)

    return jsonify([{"id": 1, "name": "There's not quality profile, you must create one in the app"}])

@app.route("/listLanguageProfiles/<mediaType>", methods=["GET"])
def listLanguageProfiles(mediaType):
    if mediaType == "serie": 
        sonarrFolder = config["ARRSettings"]["sonarrFolder"]
        sonarrAPIKey = config["APIKeys"]["sonarr"]
        sonarrURL = config["ARRSettings"]["sonarrurl"]
        sonarr = SonarrAPI(sonarrURL, sonarrAPIKey)
        languages = sonarr.get_language_profile()
        realLanguages = []
        savedIds = []
        for language in languages:
            theLanguages = language["languages"]
            for theLanguage in theLanguages:
                if theLanguage["allowed"]:
                    if theLanguage["language"]["id"] not in savedIds:
                        savedIds.append(theLanguage["language"]["id"])
                        realLanguages.append(theLanguage["language"])
        return jsonify(realLanguages)
    return jsonify([{"id": 1, "name": "There's not language profile, you must create one in the app"}])

@app.route("/addMedia", methods=["POST"])
def addMedia():
    mediaType = request.get_json()["mediaType"]
    mediaID = request.get_json()["ID"]
    qualityProfile = request.get_json()["qualityID"]
    term = request.get_json()["term"]
        

    if mediaType == "movie":
        radarrFolder = config["ARRSettings"]["radarrFolder"]
        radarrAPIKey = config["APIKeys"]["radarr"]
        radarrURL = config["ARRSettings"]["radarrurl"]
        radarr = RadarrAPI(radarrURL, radarrAPIKey)
        # get all quality : print(radarr.get_quality_profile())
        movie = radarr.lookup_movie(term=term)[int(mediaID)]
        addMovie = radarr.add_movie(movie=movie, quality_profile_id=int(qualityProfile), root_dir=radarrFolder)    
    elif mediaType == "serie":
        languageId = request.get_json()["languageId"]
        sonarrFolder = config["ARRSettings"]["sonarrFolder"]
        sonarrAPIKey = config["APIKeys"]["sonarr"]
        sonarrURL = config["ARRSettings"]["sonarrurl"]
        languageId = request.get_json()["languageId"]
        sonarr = SonarrAPI(sonarrURL, sonarrAPIKey)
        serie = sonarr.lookup_series(term=term)[int(mediaID)]
        addSerie = sonarr.add_series(series=serie, quality_profile_id=int(qualityProfile), root_dir=sonarrFolder, language_profile_id=int(languageId))
    elif mediaType == "music":
        fileType = request.get_json()["type"]
        lidarrFolder = config["ARRSettings"]["lidarrFolder"]
        lidarrAPIKey = config["APIKeys"]["lidarr"]
        lidarrURL = config["ARRSettings"]["lidarrurl"]
        lidarr = LidarrAPI(lidarrURL, lidarrAPIKey)
        #print(f"mediaID: {mediaID} | qualityProfile: {qualityProfile} | lidarrFolder: {lidarrFolder}")
        if fileType == "album":
            album = lidarr.lookup(term=term)[int(mediaID)]["album"]
            addAlbum = lidarr.add_album(album=album, quality_profile_id=int(qualityProfile), root_dir=lidarrFolder)
            print(addAlbum)
        elif fileType == "artist":
            artist = lidarr.lookup(term=term)[int(mediaID)]
            addArtist = lidarr.add_artist(artist=artist, quality_profile_id=int(qualityProfile), root_dir=lidarrFolder)
    elif mediaType == "book":
        readarrFolder = config["ARRSettings"]["readarrFolder"]
        readarrAPIKey = config["APIKeys"]["readarr"]
        readarrURL = config["ARRSettings"]["readarrurl"]
        readarr = ReadarrAPI(readarrURL, readarrAPIKey)

        addBook = readarr.add_book(db_id=int(mediaID), quality_profile_id=int(qualityProfile), root_dir=readarrFolder, book_id_type="goodreads")

    return jsonify({"status": "ok"})

@app.route("/getIMDBPoster", methods=["POST"])
def getIMDBPoster():
    jsonFile = request.get_json()
    print(jsonFile)
    if "imdbId" in jsonFile:
        imdbID = jsonFile["imdbId"]
        find = Find()
        media = find.find_by_imdb_id(imdbID)
        url = ""
        if media:
            try:
                for movie in media["movie_results"]:
                    url = "https://www.themoviedb.org/t/p/w600_and_h900_bestv2" + movie["poster_path"]
                    break
                for serie in media["tv_results"]:
                    url = "https://www.themoviedb.org/t/p/w600_and_h900_bestv2" + serie["poster_path"]
                    break
            except:
                url = "/static/img/broken.webp"
        return jsonify({"url": url})
    else:
        return jsonify({"url": "/static/img/broken.webp"})

@app.route("/getAllUsers", methods=["GET"])
def getAllUsers():
    allUsers = Users.query.filter().all()
    allUsersDict = []
    for user in allUsers:
        profilePicture = user.profilePicture
        if not os.path.exists(dir+profilePicture):
            profilePicture = f"static/img/defaultUserProfilePic.png"
        userDict = {"name": user.name, "profilePicture": profilePicture, "accountType": user.accountType, "passwordEmpty": "yes" if user.password == None else "no"}
        allUsersDict.append(userDict)
    data = {"users": allUsersDict, "status": "ok"}
    return jsonify(data)

@app.route("/login", methods=["POST"])
def login():
    global allAuthTokens
    if request.method == "POST":
        from uuid import uuid4
        authToken = str(uuid4())
        accountName = request.get_json()["name"]
        accountPassword = request.get_json()["password"]
        user = Users.query.filter_by(name=accountName).first()
        token = f"Bearer {authToken}"
        actualTimeInSeconds = int(time())
        allAuthTokens[token] = {"user": user.name, "time": actualTimeInSeconds}
        if user:
            if user.accountType == "Kid":
                return jsonify({"id": user.id, "name": user.name, "error": "None", "token": authToken})
            elif user.verify_password(accountPassword):
                return jsonify({"id": user.id, "name": user.name, "error": "None", "token": authToken})
            else:
                return jsonify({"error": "Unauthorized"})
        else:
            return jsonify({"error": "Unauthorized"})
    abort(401, "Wrong method")

@app.route("/getNumberOfAccounts")
def getNumberOfAccounts():
    allUsers = Users.query.filter().all()
    return jsonify(len(allUsers))

@app.route("/createAccount", methods=["POST"])
def createAccount():  
    accountName = request.form["name"]
    accountPassword = request.form["password"]
    accountTypeInput = request.form["type"]
    
    try:
        f = request.files['profilePicture']
        name, extension = os.path.splitext(f.filename)
        thisdirPath = dirPath.replace("\\", "//")
        profilePicture = f"/static/img/{accountName}{extension}"
        if extension == "":
            profilePicture = "/static/img/defaultUserProfilePic.png"
        else:
            f.save(f"{thisdirPath}{profilePicture}")
    except Exception as e:
        print(e)
        profilePicture = "/static/img/defaultUserProfilePic.png"

    user_exists = Users.query.filter_by(name=accountName).first()
    if user_exists:
        abort(409, "User already exists")

    new_user = Users(name=accountName, password=accountPassword, profilePicture=profilePicture, accountType=accountTypeInput)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({
        "id" : new_user.id,
        "name" : new_user.name,
    })

@app.route("/editProfil", methods=["POST"])
def editProfil():
    userName = request.form["name"]
    password = request.form["password"]
    currentUserName = request.form["currentUser"]
    try:
        f = request.files['profilePicture']
        name, extension = os.path.splitext(f.filename)
        thisdirPath = dirPath.replace("\\", "//")
        profilePicture = f"/static/img/{userName}{extension}"
        if extension == "":
            profilePicture = "/static/img/defaultUserProfilePic.png"
    except:
        profilePicture = "/static/img/defaultUserProfilePic.png"
    userToEdit = Users.query.filter_by(name=currentUserName).first()
    if userToEdit.name != userName:
        userToEdit.name = userName
        db.session.commit()
    if userToEdit.password != generate_password_hash(password) and len(password)>0:
        if password == "":
            userToEdit.password = None
        else:
            userToEdit.password = generate_password_hash(password)
        db.session.commit()
    if userToEdit.profilePicture != profilePicture and not "/static/img/defaultUserProfilePic.png" in profilePicture:
        f = request.files['profilePicture']
        f.save(f"{thisdirPath}{profilePicture}")
        userToEdit.profilePicture = profilePicture
        db.session.commit()
    return jsonify({
        "id" : userToEdit.id,
        "name" : userToEdit.name,
    })

@app.route("/getProfile/<username>")
def getProfile(username):
    user = Users.query.filter_by(name=username).first()
    profilePicture = user.profilePicture
    if not os.path.exists(dir+profilePicture):
        profilePicture = f"static/img/defaultUserProfilePic.png"
    userDict = {"name": user.name, "profilePicture": profilePicture, "accountType": user.accountType}
    return jsonify(userDict)

@app.route("/chunkCaptionSerie/<language>/<index>/<episodeId>.vtt", methods=["GET"])
def chunkCaptionSerie(language, index, episodeId):
    episode = Episodes.query.filter_by(episodeId=episodeId).first()
    season = Seasons.query.filter_by(seasonId=episode.seasonId).first()
    serie = Series.query.filter_by(id=season.serie).first()
    library = serie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    episodePath = episode.slug
    episodePath = episodePath.replace("\\", "/")
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

@app.route("/saveSettings", methods=["GET", "POST"])
def saveSettings():
    global clientID, clientSecret
    config = configparser.ConfigParser()
    config.read(os.path.join(dir, 'config.ini'))
    body = request.get_json()
    language = body["language"]
    tmdbApiKey = body["tmdbKey"]
    igdbSecretKey = body["igdbSecret"]
    igdbClientId = body["igdbID"]

    radarrAdress = body["radarrAdress"]
    radarrfolder = body["radarrFolder"]
    radarrApiKey = body["radarrAPI"]
    sonarrAdress = body["sonarrAdress"]
    sonarrfolder = body["sonarrFolder"]
    sonarrApiKey = body["sonarrAPI"]
    readarrAdress = body["readarrAdress"]
    readarrfolder = body["readarrFolder"]
    readarrApiKey = body["readarrAPI"]
    lidarrAdress = body["lidarrAdress"]
    lidarrfolder = body["lidarrFolder"]
    lidarrApiKey = body["lidarrAPI"]

    if radarrAdress != "":
        if radarrAdress.startswith("https://"):
            radarrAdress = radarrAdress.replace("https://", "http://")
        if not radarrAdress.startswith("http://"):
            radarrAdress = f"http://{radarrAdress}"
        config.set("ARRSettings", "radarrurl", radarrAdress)
    if radarrfolder != "":
        radarrfolder = radarrfolder.replace("\\", "/")
        if not radarrfolder.endswith("/"):
            radarrfolder = f"{radarrfolder}/"
        config.set("ARRSettings", "radarrfolder", radarrfolder)
    if radarrApiKey != "":
        config.set("APIKeys", "radarr", radarrApiKey)

    if sonarrAdress != "":
        if sonarrAdress.startswith("https://"):
            sonarrAdress = sonarrAdress.replace("https://", "http://")
        if not sonarrAdress.startswith("http://"):
            sonarrAdress = f"http://{sonarrAdress}"
        config.set("ARRSettings", "sonarrurl", sonarrAdress)
    if sonarrfolder != "":
        sonarrfolder = sonarrfolder.replace("\\", "/")
        if not sonarrfolder.endswith("/"):
            sonarrfolder = f"{sonarrfolder}/"
        config.set("ARRSettings", "sonarrfolder", sonarrfolder)
    if sonarrApiKey != "":
        config.set("APIKeys", "sonarr", sonarrApiKey)

    if readarrAdress != "":
        if readarrAdress.startswith("https://"):
            readarrAdress = readarrAdress.replace("https://", "http://")
        if not readarrAdress.startswith("http://"):
            readarrAdress = f"http://{readarrAdress}"
        config.set("ARRSettings", "readarrurl", readarrAdress)
    if readarrfolder != "":
        readarrfolder = readarrfolder.replace("\\", "/")
        if not readarrfolder.endswith("/"):
            readarrfolder = f"{readarrfolder}/"
        config.set("ARRSettings", "readarrfolder", readarrfolder)
    if readarrApiKey != "":
        config.set("ARRSettings", "readarrurl", readarrAdress)

    if lidarrAdress != "":
        if lidarrAdress.startswith("https://"):
            lidarrAdress = lidarrAdress.replace("https://", "http://")
        if not lidarrAdress.startswith("http://"):
            lidarrAdress = f"http://{lidarrAdress}"
        config.set("ARRSettings", "lidarrurl", lidarrAdress)
    if lidarrfolder != "":
        lidarrfolder = lidarrfolder.replace("\\", "/")
        if not lidarrfolder.endswith("/"):
            lidarrfolder = f"{lidarrfolder}/"
        config.set("ARRSettings", "lidarrfolder", lidarrfolder)
    if lidarrApiKey != "":
        config.set("ARRSettings", "lidarrurl", lidarrAdress)

    
    if language != "undefined":
        config.set("ChocolateSettings", "language", language)
    if tmdbApiKey != "":
        config.set("APIKeys", "TMDB", tmdbApiKey)
        tmdb.api_key = tmdbApiKey
    if igdbClientId != "" and igdbSecretKey != "":
        config.set("APIKeys", "igdbid", igdbClientId)
        config.set("APIKeys", "igdbsecret", igdbSecretKey)
        clientID = igdbClientId
        clientSecret = igdbSecretKey
    try:
        allowDownload = body["allowDownloadsCheckbox"]
        if allowDownload == "on":
            config.set("ChocolateSettings", "allowdownload", "true")
        else:
            config.set("ChocolateSettings", "allowdownload", "false")
    except:
        config.set("ChocolateSettings", "allowdownload", "false")
    with open(os.path.join(dir, 'config.ini'), "w") as conf:
        config.write(conf)
    return redirect(url_for("settings"))

def userInLib(user, lib):
    if type(lib) != dict:
        lib = lib.__dict__
    if type(user) != str:
        if type(user) != dict:
            user = user.__dict__
        user = user["name"]

    if lib["availableFor"] == None or user in lib["availableFor"]:
        return True
    return False

@app.route("/getAllMovies/<library>/<username>", methods=["GET"])
def getAllMovies(library, username):
    movies = Movies.query.filter_by(libraryName=library).all()
    theLib = Libraries.query.filter_by(libName=library).first()
    user = Users.query.filter_by(name=username).first()
    userInTheLib = userInLib(user, theLib)
    if movies is None or user is None or not userInTheLib:
        abort(404)
    moviesDict = [ movie.__dict__ for movie in movies ]
    #get the user from the database
    #get the user type
    userType = user.accountType
    for movie in moviesDict:
        del movie["_sa_instance_state"]
    
    if userType in ["Kid", "Teen"]:
        for movie in moviesDict:
            if movie["adult"] == "True":
                moviesDict.remove(movie)

    moviesDict = sorted(moviesDict, key=lambda k: k['realTitle'])
    
    return json.dumps(moviesDict, ensure_ascii=False)

@app.route("/getAllBooks/<library>", methods=["GET"])
def getAllBooks(library):
    theLibrary = Libraries.query.filter_by(libName=library).first()
    books = Books.query.filter_by(libraryName=library).all()
    booksDict = [ book.__dict__ for book in books ]
    for book in booksDict:
        del book["_sa_instance_state"]

    booksDict = sorted(booksDict, key=lambda k: k['title'])

    return json.dumps(booksDict, ensure_ascii=False)

@app.route("/getAllLibraries", methods=["GET"])
def getAllLibraries():
    libraries = Libraries.query.all()
    librariesDict = [ library.__dict__ for library in libraries ]
    for library in librariesDict:
        del library["_sa_instance_state"]
    return json.dumps(librariesDict, ensure_ascii=False)

@app.route("/getAllLibraries/<user>", methods=["GET"])
def getAllLibrariesForUserOrType(user):
    if user == "undefined":
        abort(404)

    libraries = Libraries.query.filter_by().all()
    librariesDict = [ library.__dict__ for library in libraries ]
    for library in librariesDict:
        del library["_sa_instance_state"]
    for library in librariesDict:
        if library["availableFor"] != None:
            if user not in library["availableFor"]:
                librariesDict.remove(library)

    libraries = sorted(librariesDict, key=lambda k: k['libName'])
    libraries = sorted(librariesDict, key=lambda k: k['libType'])

    return json.dumps(libraries, ensure_ascii=False)

@app.route("/createLib", methods=["POST"])
def createLib():
    theRequest = request.get_json()
    libName = theRequest["libName"]
    libPath = theRequest["libPath"]
    libType = theRequest["libType"]
    libUsers = theRequest["libUsers"]

    if libUsers == "":
        libUsers = None

    icons = {
        "movies": "film",
        "series": "videocam",
        "games": "game-controller",
        "tv": "tv",
        "other": "desktop",
        "books": "book",
        }

    functionToCall = {
        "movies": getMovies,
        "series": getSeries,
        "games": getGames,
        "other": getOthersVideos,
        "books": getBooks,
    }

    libPath = libPath.replace("\\", "/")

    exists = Libraries.query.filter_by(libName=libName).first() is not None
    if not exists:
        newLib = Libraries(libName=libName, libFolder=libPath, libType=libType, libImage=icons[libType], availableFor=libUsers)
        db.session.add(newLib)
        db.session.commit()
        try:
            functionToCall[libType](libName)
        except:
            pass

        return jsonify({"error": "worked"})
    else:
        abort(400)

@app.route("/editLib/<libName>", methods=["POST"])
def editLib(libName):
    theRequest = request.get_json()
    libPath = theRequest["libPath"]
    libType = theRequest["libType"]
    libUsers = theRequest["libUsers"]

    if libUsers == "" or libUsers == None or libUsers == "undefined":
        libUsers = None


    libPath = libPath.replace("\\", "/")

    lib = Libraries.query.filter_by(libName=libName).first()
    if lib is None:
        abort(400)

    lib.libFolder = libPath
    lib.libType = libType
    lib.availableFor = libUsers
    db.session.commit()
    lib = Libraries.query.filter_by(libName=libName).first()

    abort(200)

@app.route("/deleteLib/<libName>", methods=["POST"])
def deleteLib(libName):
    lib = Libraries.query.filter_by(libName=libName).first()

    if lib is None:
        abort(400)

    db.session.delete(lib)

    libType = lib.libType

    if libType == "movies":
        allMovies = Movies.query.filter_by(libraryName=libName).all()
        for movie in allMovies:
            db.session.delete(movie)
    elif libType == "series":
        allSeries = Series.query.filter_by(libraryName=libName).all()
        for serie in allSeries:
            seasons = Seasons.query.filter_by(serie=serie.id).all()
            for season in seasons:
                episodes = Episodes.query.filter_by(seasonId=season.seasonId).all()
                for episode in episodes:
                    db.session.delete(episode)
                db.session.delete(season)
            db.session.delete(serie)
    elif libType == "games":
        allGames = Games.query.filter_by(libraryName=libName).all()
        for game in allGames:
            db.session.delete(game)
    elif libType == "other":
        allOther = OthersVideos.query.filter_by(libraryName=libName).all()
        for other in allOther:
            db.session.delete(other)

    db.session.commit()
    return redirect(url_for("settings"))

@app.route("/getAllSeries/<library>/<username>", methods=["GET"])
def getAllSeries(library, username):
    series = Series.query.filter_by(libraryName=library).all()
    if series is None:
        abort(404)
    series = [ serie.__dict__ for serie in series ]
    user = Users.query.filter_by(name=username).first()
    userType = user.accountType
    if userType in ["Kid", "Teen"]:
        for serie in series:
            if serie["adult"] == "True":
                series.remove(serie)
                
    seriesDict = { serie["name"]: serie for serie in series }

    seriesDict = {k: v for k, v in sorted(seriesDict.items(), key=lambda item: item[1]["name"])}

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


@app.route("/getMovieData/<movieId>", methods=["GET"])
def getMovieData(movieId):
    exists = Movies.query.filter_by(id=movieId).first() is not None
    if exists:
        movie = Movies.query.filter_by(id=movieId).first().__dict__
        del movie["_sa_instance_state"]
        movie["similarMovies"] = getSimilarMovies(movieId)
        return json.dumps(movie, ensure_ascii=False)
    else:
        abort(404)

@app.route("/getOtherData/<videoHash>", methods=["GET"])
def getOtherData(videoHash):
    exists = OthersVideos.query.filter_by(videoHash=videoHash).first() is not None
    if exists:
        other = OthersVideos.query.filter_by(videoHash=videoHash).first().__dict__
        del other["_sa_instance_state"]
        return json.dumps(other, ensure_ascii=False)
    else:
        abort(404)

@app.route("/getSerieData/<serieId>", methods=["GET"])
def getSeriesData(serieId):
    exists = Series.query.filter_by(id=serieId).first() is not None
    if exists:
        serie = Series.query.filter_by(id=serieId).first().__dict__
        serie["seasons"] = getSerieSeasons(serie["id"])
        del serie["_sa_instance_state"]
        return json.dumps(serie, ensure_ascii=False)
    else:
        abort(404)

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
def home():
    html = "<h1>Chocolate Server</h1>"
    return html

def transform(obj):
    if isinstance(obj, AsObj):
        return str(obj)
    return obj.replace('"', '\\"')


@app.route("/editMovie/<title>/<library>", methods=["GET", "POST"])
def editMovie(title, library):
    config = configparser.ConfigParser()
    config.read(os.path.join(dir, 'config.ini'))
    print(title)
    if request.method == "GET":
        theMovie = Movies.query.filter_by(title=title, libraryName=library).first()
        theMovie = theMovie.__dict__
        del theMovie["_sa_instance_state"]
        movieName = theMovie["title"]
        tmdb = TMDb()
        tmdb.language = config["ChocolateSettings"]["language"].lower()
        movie = Movie()
        movieInfo = movie.search(movieName)
        movieInfo = sorted(movieInfo, key=lambda k: k['popularity'], reverse=True)
        
        realMovies = []
        for theMovie in movieInfo:
            acceptedTypes = [str, int, list, dict, float, bool]
            theMovie = theMovie.__dict__
            for key in theMovie:
                if type(theMovie[key]) not in acceptedTypes:
                    theMovie[key] = str(theMovie[key])
            realMovies.append(theMovie)


        movies = { "movies": realMovies }

        return jsonify(movies)

    newMovieID = request.get_json()["newMovieID"]
    theMovie = Movies.query.filter_by(title=title, libraryName=library).first()
    tmdb = TMDb()
    tmdb.language = config["ChocolateSettings"]["language"].lower()
    movie = Movie()
    movieInfo = movie.details(newMovieID)
    theMovie.id = newMovieID
    theMovie.realTitle = movieInfo.title
    theMovie.description = movieInfo.overview
    theMovie.note = movieInfo.vote_average
    date = movieInfo.release_date

    try:
        date = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError as e:
        date = "Unknown"
    except UnboundLocalError:
        date = "Unknown"        
    
    theMovie.date = date

    
    bandeAnnonce = movieInfo.videos.results

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
    
    theMovie.bandeAnnonceUrl = bandeAnnonceUrl
    theMovie.adult = str(movieInfo.adult)

    
    alternativesNames = []
    actualTitle = movieInfo.title
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
                
    officialAlternativeNames = movie.alternative_titles(movie_id=theMovie.id).titles
    if officialAlternativeNames is not None:
        for officialAlternativeName in officialAlternativeNames:
            alternativesNames.append(officialAlternativeName.title)

    alternativesNames = list(dict.fromkeys(alternativesNames))

    alternativesNames = ",".join(alternativesNames)

    theMovie.alternativesNames = alternativesNames

    theMovie.vues = str({})

    movieGenre = []
    genre = movieInfo.genres
    for genreInfo in genre:
        movieGenre.append(genreInfo.name)
    movieGenre = json.dumps(movieGenre)
    
    theMovie.genre = movieGenre

    casts = movieInfo.casts.cast[:5]
    theCast = []
    for cast in casts:
        characterName = cast.character
        actorId = cast.id
        actorImage = f"https://www.themoviedb.org/t/p/w600_and_h900_bestv2{cast.profile_path}"
        if not os.path.exists(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.webp"):
            with open(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.png", "wb") as f:
                f.write(requests.get(actorImage).content)
            try:
                img = Image.open(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.png")
                img = img.save(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.webp", "webp")
                os.remove(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.png")
            except Exception as e:
                os.rename(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.png", f"{dirPath}/static/img/mediaImages/Actor_{actorId}.webp")

        actorImage = f"/static/img/mediaImages/Actor_{actorId}.webp"
        actor = [cast.name, characterName, actorImage, cast.id]
        if actor not in theCast:
            theCast.append(actor)
        else:
            break
        person = Person()
        p = person.details(cast.id)
        exists = Actors.query.filter_by(actorId=cast.id).first() is not None
        if not exists:
            actor = Actors(name=cast.name, actorImage=actorImage, actorDescription=p.biography, actorBirthDate=p.birthday, actorBirthPlace=p.place_of_birth, actorPrograms=f"{theMovie.id}", actorId=actorId)
            db.session.add(actor)
            db.session.commit()
        else:
            actor = Actors.query.filter_by(actorId=cast.id).first()
            actor.actorPrograms = f"{actor.actorPrograms} {theMovie.id}"
            db.session.commit()

    theCast = theCast
    theCast = json.dumps(theCast)
    theMovie.cast = theCast

    movieCoverPath = f"https://image.tmdb.org/t/p/original{movieInfo.poster_path}"
    banniere = f"https://image.tmdb.org/t/p/original{movieInfo.backdrop_path}"

    try:
        os.remove(f"{dirPath}/static/img/mediaImages/{newMovieID}_cover.webp")
    except FileNotFoundError:
        pass
    try:
        os.remove(f"{dirPath}/static/img/mediaImages/{newMovieID}_cover.png")
    except FileNotFoundError:
        pass
    with open(f"{dirPath}/static/img/mediaImages/{newMovieID}_cover.png", "wb") as f:
        f.write(requests.get(movieCoverPath).content)
    try:
        img = Image.open(f"{dirPath}/static/img/mediaImages/{newMovieID}_cover.png")
        img.save(f"{dirPath}/static/img/mediaImages/{newMovieID}_cover.webp", "webp")
        os.remove(f"{dirPath}/static/img/mediaImages/{newMovieID}_cover.png")
        movieCoverPath = f"/static/img/mediaImages/{newMovieID}_cover.webp"
    except:
        os.rename(f"{dirPath}/static/img/mediaImages/{newMovieID}_cover.png", f"{dirPath}/static/img/mediaImages/{newMovieID}_cover.webp")
        movieCoverPath = "/static/img/broken.webp"
    try:
        os.remove(f"{dirPath}/static/img/mediaImages/{newMovieID}_Banner.webp")
    except FileNotFoundError:
        pass
    with open(f"{dirPath}/static/img/mediaImages/{newMovieID}_Banner.png", "wb") as f:
        f.write(requests.get(banniere).content)
    if movieInfo.backdrop_path == None:
        banniere = f"https://image.tmdb.org/t/p/original{movieInfo.backdrop_path}"
        if banniere != "https://image.tmdb.org/t/p/originalNone":
            with open(f"{dirPath}/static/img/mediaImages/{newMovieID}_Banner.png", "wb") as f:
                f.write(requests.get(banniere).content)
        else:
            banniere = "/static/img/broken.webp"
    try:
        img = Image.open(f"{dirPath}/static/img/mediaImages/{newMovieID}_Banner.png")
        img.save(f"{dirPath}/static/img/mediaImages/{newMovieID}_Banner.webp", "webp")
        os.remove(f"{dirPath}/static/img/mediaImages/{newMovieID}_Banner.png")
        banniere = f"/static/img/mediaImages/{newMovieID}_Banner.webp"
    except:
        os.rename(f"{dirPath}/static/img/mediaImages/{newMovieID}_Banner.png", f"{dirPath}/static/img/mediaImages/{newMovieID}_Banner.webp")
        banniere = "/static/img/brokenBanner.webp"

    theMovie.cover = movieCoverPath
    theMovie.banner = banniere
    db.session.commit()

    return jsonify({"status": "success"})

@app.route("/editSerie/<title>/<library>", methods=["GET", "POST"])
def editSerie(title, library):
    config = configparser.ConfigParser()
    config.read(os.path.join(dir, 'config.ini'))

    if request.method == "GET":
        serie = Series.query.filter_by(originalName=title, libraryName=library).first().__dict__
        
        del serie["_sa_instance_state"]
        serieName = serie["originalName"]
        tmdb = TMDb()
        tmdb.language = config["ChocolateSettings"]["language"].lower()
        series = TV()
        serieInfo = series.search(serieName)
        serieInfo = sorted(serieInfo, key=lambda k: k['popularity'], reverse=True)

        
        realSeries = []
        for theSerie in serieInfo:
            acceptedTypes = [str, int, list, dict, float, bool]
            theSerie = theSerie.__dict__
            for key in theSerie:
                if type(theSerie[key]) not in acceptedTypes:
                    theSerie[key] = str(theSerie[key])
            realSeries.append(theSerie)

        return json.dumps(realSeries, default=transform, ensure_ascii=False, indent=4)


    elif request.method == "POST":
            serieId = request.get_json()["newSerieID"]
            theSerie = Series.query.filter_by(originalName=title, libraryName=library).first()

            if theSerie.id == serieId:
                return jsonify({"status": "success"})

            allSeasons = Seasons.query.filter_by(serie=serieId).all()
            for season in allSeasons:
                cover = f"{dirPath}{season.seasonCoverPath}"
                try:
                    os.remove(cover)
                except FileNotFoundError:
                    pass
                episodes = Episodes.query.filter_by(seasonId=season.seasonNumber).all()
                for episode in episodes:
                    cover = f"{dirPath}{episode.episodeCoverPath}"
                    os.remove(cover)
                    db.session.delete(episode)
                db.session.delete(season)
            db.session.commit()

            tmdb = TMDb()
            tmdb.language = config["ChocolateSettings"]["language"].lower()
            show = TV()
            details = show.details(serieId)
            res = details

            name = details.name
            serieCoverPath = f"https://image.tmdb.org/t/p/original{res.poster_path}"
            banniere = f"https://image.tmdb.org/t/p/original{res.backdrop_path}"
            if not os.path.exists(f"{dirPath}/static/img/mediaImages/{serieId}_Cover.webp"):
                with open(f"{dirPath}/static/img/mediaImages/{serieId}_Cover.png","wb") as f:
                    f.write(requests.get(serieCoverPath).content)

                img = Image.open(f"{dirPath}/static/img/mediaImages/{serieId}_Cover.png")
                img = img.save(f"{dirPath}/static/img/mediaImages/{serieId}_Cover.webp", "webp")
                os.remove(f"{dirPath}/static/img/mediaImages/{serieId}_Cover.png")
            else:
                os.remove(f"{dirPath}/static/img/mediaImages/{serieId}_Cover.webp")
                with open(f"{dirPath}/static/img/mediaImages/{serieId}_Cover.png","wb") as f:
                    f.write(requests.get(serieCoverPath).content)

                img = Image.open(f"{dirPath}/static/img/mediaImages/{serieId}_Cover.png")
                img = img.save(f"{dirPath}/static/img/mediaImages/{serieId}_Cover.webp", "webp")
                os.remove(f"{dirPath}/static/img/mediaImages/{serieId}_Cover.png")
            

            if not os.path.exists(f"{dirPath}/static/img/mediaImages/{serieId}_Banner.webp"):
                with open(f"{dirPath}/static/img/mediaImages/{serieId}_Banner.png","wb") as f:
                    f.write(requests.get(banniere).content)

                img = Image.open(f"{dirPath}/static/img/mediaImages/{serieId}_Banner.png")
                img = img.save(f"{dirPath}/static/img/mediaImages/{serieId}_Banner.webp", "webp")
                os.remove(f"{dirPath}/static/img/mediaImages/{serieId}_Banner.png")
            else:
                os.remove(f"{dirPath}/static/img/mediaImages/{serieId}_Banner.webp")
                with open(f"{dirPath}/static/img/mediaImages/{serieId}_Banner.png","wb") as f:
                    f.write(requests.get(banniere).content)
                img = Image.open(f"{dirPath}/static/img/mediaImages/{serieId}_Banner.png")
                img = img.save(f"{dirPath}/static/img/mediaImages/{serieId}_Banner.webp", "webp")
                os.remove(f"{dirPath}/static/img/mediaImages/{serieId}_Banner.png")

            banniere = f"/static/img/mediaImages/{serieId}_Banner.webp"
            serieCoverPath = f"/static/img/mediaImages/{serieId}_Cover.webp"
            description = res["overview"]
            note = res.vote_average
            date = res.first_air_date
            cast = details.credits.cast
            runTime = details.episode_run_time
            duration = ""
            for i in range(len(runTime)):
                if i != len(runTime) - 1:
                    duration += f"{str(runTime[i])}:"
                else:
                    duration += f"{str(runTime[i])}"
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
                actorName = actor.name.replace("/", "")
                actorId = actor.id
                actorImage = f"https://image.tmdb.org/t/p/original{actor.profile_path}"
                if not os.path.exists(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.webp"):
                    with open(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.png", "wb") as f:
                        f.write(requests.get(actorImage).content)
                    img = Image.open(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.png")
                    img = img.save(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.webp", "webp")
                    os.remove(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.png")
                else:
                    os.remove(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.webp")
                    with open(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.png", "wb") as f:
                        f.write(requests.get(actorImage).content)
                    img = Image.open(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.png")
                    img = img.save(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.webp", "webp")
                    os.remove(f"{dirPath}/static/img/mediaImages/Actor_{actorId}.png")

                actorImage = f"/static/img/mediaImages/Actor_{actorId}.webp"
                actorCharacter = actor.character
                actor.profile_path = str(actorImage)
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
            allSeriesPath = Libraries.query.filter_by(libName=library).first().libFolder
            serieModifiedTime = os.path.getmtime(f"{allSeriesPath}/{theSerie.originalName}")

            newCast = json.dumps(newCast[:5])
            genreList = json.dumps(genreList)
            isAdult = str(details["adult"])
            theSerie.id = serieId
            theSerie.name = name
            theSerie.genre = genreList
            theSerie.duration = duration
            theSerie.description = description
            theSerie.cast = newCast
            theSerie.bandeAnnonceUrl = bandeAnnonceUrl
            theSerie.serieCoverPath = serieCoverPath
            theSerie.banniere = banniere
            theSerie.note = note
            theSerie.date = date
            theSerie.serieModifiedTime = serieModifiedTime
            theSerie.adult = isAdult
            theSerie.libraryName = library
            
            db.session.commit()
            getSeries(library)

            return jsonify({"status": "success"})
            

@app.route("/getSeasonData/<seasonId>/", methods=["GET"])
def getSeasonData(seasonId):
    season = Seasons.query.filter_by(seasonId=seasonId).first()
    if season is None:
        abort(404)
    episodes = Episodes.query.filter_by(seasonId=seasonId).all()
    episodesDict = {}
    for episode in episodes:
        episodesDict[episode.episodeNumber] = dict(episode.__dict__)
        del episodesDict[episode.episodeNumber]["_sa_instance_state"]
    season = season.__dict__
    del season["_sa_instance_state"]
    season["episodes"] = episodesDict
    return json.dumps(season, ensure_ascii=False, default=str)

@app.route("/getEpisodeData/<episodeId>/", methods=["GET"])
def getEpisodeData(episodeId):
    episode = Episodes.query.filter_by(episodeId=episodeId).first()
    if episode is None:
        abort(404)
    episode = episode.__dict__
    season = episode["seasonId"]
    episodeNumber = episode["episodeNumber"]
    allEpisodes = Episodes.query.filter_by(seasonId=season).all()
    allEpisodesList = []
    for episode in allEpisodes:
        allEpisodesList.append(dict(episode.__dict__))
    allEpisodesList = sorted(allEpisodesList, key=lambda k: k['episodeNumber'])
    episodeIndex = allEpisodesList.index([x for x in allEpisodesList if x["episodeNumber"] == episodeNumber][0])
    previousEpisode, nextEpisode = None, None

    if episodeIndex != 0:
        previousEpisode = allEpisodesList[episodeIndex - 1]["episodeId"]
    if episodeIndex != len(allEpisodesList) - 1:
        nextEpisode = allEpisodesList[episodeIndex + 1]["episodeId"]
    
    newEpisodeData = {}
    for k, v in episode.__dict__.items():
        newEpisodeData[k] = v

    del newEpisodeData["_sa_instance_state"]
    newEpisodeData["previousEpisode"] = previousEpisode
    newEpisodeData["nextEpisode"] = nextEpisode

    return json.dumps(newEpisodeData, ensure_ascii=False, default=str)

@app.route("/rescan/<library>", methods=["GET"])
def rescan(library):
    exists = Libraries.query.filter_by(libName=library).first() is not None
    if exists:
        library = Libraries.query.filter_by(libName=library).first().__dict__
        if library["libType"] == "series":
            getSeries(library["libName"])
        elif library["libType"] == "movies":
            getMovies(library["libName"])
        elif library["libType"] == "games":
            getGames(library["libName"])
        elif library["libType"] == "other":
            getOthersVideos(library["libName"])
        elif library["libType"] == "books":
            getBooks(library["libName"])
        return jsonify(True)
    return jsonify(False)

@app.route("/rescanAll", methods=["GET"])
def rescanAll():
    library = Libraries.query.all()
    for lib in library:
        lib = lib.__dict__
        if lib["libType"] == "series":
            getSeries(lib["libName"])
        elif lib["libType"] == "movies":
            getMovies(lib["libName"])
        elif lib["libType"] == "games":
            getGames(lib["libName"])
        elif lib["libType"] == "other":
            getOthersVideos(lib["libName"])
    return jsonify(True)

@app.route("/bookUrl/<id>")
def bookUrl(id):
    book = Books.query.filter_by(id=id).first()
    if book is None:
        abort(404)
    book = book.__dict__
    return send_file(book["slug"], as_attachment=True)


@app.route("/bookUrl/<id>/<page>")
def bookUrlPage(id, page):
    book = Books.query.filter_by(id=id).first()
    if book is None:
        abort(404)
    book = book.__dict__
    bookType = book["bookType"]
    bookSlug = book["slug"]
    available = ["PDF", "CBZ", "CBR", "EPUB"]
    if bookType in available:
        base64URL = ""
        if bookType == "PDF":
            import fitz
            pdfDoc = fitz.open(bookSlug)
            # Récupérez la page demandée
            page = pdfDoc[int(page)]
            # Créez une image à partir de la page
            pix = page.get_pixmap()
            # Encodez l'image en base64
            base64_img = pix.tobytes()
            base64URL = base64.b64encode(base64_img).decode("utf-8")

        elif bookType == "CBZ":
            with zipfile.ZipFile(bookSlug, 'r') as zip:
                image_file = zip.namelist()[int(page)]
                if image_file.endswith(".jpg") or image_file.endswith(".jpeg") or image_file.endswith(".png"):
                    with zip.open(image_file) as image:
                        base64Image = base64.b64encode(image.read()).decode("utf-8")
                        return base64Image
                elif image_file.endswith("/"):
                    with zip.open(file) as folder:
                        image_file = zip.namelist()[int(page)]
                        if image_file.endswith(".jpg") or image_file.endswith(".png"):
                            with zip.open(image_file) as image:
                                base64Image = base64.b64encode(image.read()).decode("utf-8")
                                base64URL = base64Image
        
        elif bookType == "CBR":
            with rarfile.RarFile(bookSlug, 'r') as rar:
                image_file = rar.infolist()[int(page)]
                if image_file.filename.endswith(".jpg") or image_file.filename.endswith(".jpeg") or image_file.filename.endswith(".png"):
                    with rar.open(image_file) as image:
                        base64Image = base64.b64encode(image.read()).decode("utf-8")
                        return base64Image
                elif image_file.filename.endswith("/"):
                    with rar.open(file) as folder:
                        for file in rar.infolist():
                            if file.filename.endswith(".jpg") or file.filename.endswith(".png"):
                                # Ouvre le fichier image
                                with rar.open(file) as image:
                                    base64Image = base64.b64encode(image.read()).decode("utf-8")
                                    base64URL = base64Image

        elif bookType == "EPUB":
            import fitz
            pdfDoc = fitz.open(bookSlug)
            # Récupérez la page demandée
            page = pdfDoc[int(page)]
            # Créez une image à partir de la page
            pix = page.get_pixmap()
            # Encodez l'image en base64
            base64_img = pix.tobytes()
            base64URL = base64.b64encode(base64_img).decode("utf-8")

        data = base64URL.split(",")[1]
        binary_data = base64.b64decode(data)
        image = Image.open(io.BytesIO(binary_data))
        width, height = image.size
        new_height = int(height * (300.0 / width))
        image = image.resize((300, new_height), resample=Image.LANCZOS)
        buffered = io.BytesIO()
        try:
            image.save(buffered, format="WEBP", quality=75)
        except:
            image.save(buffered, format="PNG", quality=75)
        img_str = base64.b64encode(buffered.getvalue()).decode("ascii")
        
        return img_str
    else:
        abort(404, "Book type not supported")
                    
@app.route("/bookData/<id>")
def bookData(id):
    book = Books.query.filter_by(id=id).first().__dict__
    del book["_sa_instance_state"]
    bookType = book["bookType"]
    bookSlug = book["slug"]
    nbPages = 0
    if bookType == "PDF":
        with open(bookSlug, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            nbPages = len(pdf_reader.pages)
    elif bookType == "CBZ":
        with zipfile.ZipFile(bookSlug, 'r') as zip:
            nbPages = len(zip.namelist())
    elif bookType == "CBR":
        with rarfile.RarFile(bookSlug, 'r') as rar:
            nbPages = len(rar.infolist())
    book["nbPages"] = nbPages
    return json.dumps(book, ensure_ascii=False, default=str)


@app.route("/downloadOther/<videoHash>")
def downloadOther(videoHash):
    video = OthersVideos.query.filter_by(videoHash=videoHash).first()
    video = video.__dict__
    del video["_sa_instance_state"]
    return send_file(video["slug"], as_attachment=True)

def sortByEpisodeNumber(ep):
    return int(ep["title"][1:])

@app.route("/getAllOther/<library>/<user>")
def getAllOther(library, user):
    theLib = Libraries.query.filter_by(libName=library).first()
    user = Users.query.filter_by(name=user).first()
    userInTheLib = userInLib(user, theLib)
    if theLib is None or user is None or not userInTheLib:
        return jsonify([])

    other = OthersVideos.query.filter_by(libraryName=theLib.libName).all()
    otherDict = [ video.__dict__ for video in other ]

    for video in otherDict:
        del video["_sa_instance_state"]

    otherDict = sorted(otherDict, key=sortByEpisodeNumber)

    return json.dumps(otherDict, ensure_ascii=False, default=str)

@app.route("/getTv/<library>/<id>")
def getTv(library, id):
    if id != "undefined":
        library = Libraries.query.filter_by(libName=library).first()
        libFolder = library.libFolder

        if is_valid_url(libFolder):
            m3u = requests.get(libFolder).text
            m3u = m3u.split("\n")
        else:
            with open(libFolder, "r", encoding="utf-8") as f:
                m3u = f.readlines()
        m3u.pop(0)
        for ligne in m3u:
            if not ligne.startswith(("#EXTINF", "http")):
                m3u.remove(ligne)
        line = m3u[int(id)]
        nextLine = m3u[int(id)+1]
        if line.startswith("#EXTINF"):
            line = nextLine
        try:
            channelName = line.split(",")[1].replace("\n", "")
        except IndexError:
            channelName = "Channel"
        return json.dumps({"channelURL": line, "channelName": channelName}, ensure_ascii=False, default=str)
    return json.dumps({"channelURL": "", "channelName": ""}, ensure_ascii=False, default=str)

@app.route("/getChannels/<library>")
def getChannels(library):
    library = Libraries.query.filter_by(libName=library).first()
    if not library:
        abort(404, "Library not found")
    libFolder = library.libFolder
    #open the m3u file
    try:
        with open(libFolder, "r", encoding="utf-8") as f:
            m3u = f.readlines()
    except OSError:
        libFolder = libFolder.replace("\\", "/")
        m3u = requests.get(libFolder).text
        m3u = m3u.split("\n")        
    #remove the first line
    m3u.pop(0)
    while m3u[0] == "\n":
        m3u.pop(0)

    #get the channels by getting 2 lines at a time
    channels = []
    for i in m3u:
        if not i.startswith(("#EXTINF", "http")):
            m3u.remove(i)
        elif i == "\n":
            m3u.remove(i)
    for i in range(0, len(m3u)-1, 2):
        data = {}
        try:
            data["name"] = m3u[i].split(",")[-1].replace("\n", "")
            work = True
        except:
            work = False
        if work:
            data["url"] = m3u[i+1].replace("\n", "")
            data["channelID"] = i
            tvg_id_regex = r'tvg-id="(.+?)"'
            tvg_id = None
            match = re.search(tvg_id_regex, m3u[i])
            if match:
                tvg_id = match.group(1)
                data["id"] = tvg_id

            tvg_logo_regex = r'tvg-logo="(.+?)"'
            match = re.search(tvg_logo_regex, m3u[i])
            if match and match.group(1) != '" group-title=':
                tvg_logo = match.group(1)
                data["logo"] = tvg_logo
            else:
                brokenPath = ""
                data["logo"] = brokenPath
                #print(data["logo"])
            channels.append(data)
    #order the channels by name
    channels = sorted(channels, key=lambda k: k['name'])
    return jsonify(channels)

def is_valid_url(url):
    try:
        response = requests.get(url)
        return response.status_code == requests.codes.ok
    except requests.exceptions.RequestException:
        return False

@app.route("/getAllConsoles/<library>")
def getAllConsoles(library):
    consoles = Games.query.filter_by(libraryName=library).all()
    if not consoles:
        abort(404)
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


@app.route("/getGames/<consoleName>")
def getGamesFor(consoleName):
    if consoleName != None:
        consoleName = consoleName.replace("%20", " ")
        consoles = {"Gameboy": "GB", "Gameboy Advance": "GBA", "Gameboy Color": "GBC", "Nintendo 64": "N64", "Nintendo Entertainment System": "NES", "Nintendo DS": "NDS", "Super Nintendo Entertainment System": "SNES", "Sega Mega Drive": "Sega Mega Drive", "Sega Master System": "Sega Master System", "Sega Saturn": "Sega Saturn", "PS1": "PS1"}
        games = Games.query.filter_by(console=consoles[consoleName]).all()
        if not games:
            abort(404)
        gamesDict = [ game.__dict__ for game in games ]
        for game in gamesDict:
            del game["_sa_instance_state"]
        return json.dumps(gamesDict, ensure_ascii=False, default=str)
    else:
        return json.dumps({"response": "Not Found"}, ensure_ascii=False, default=str)

@app.route("/gameData/<gameId>")
def gameData(gameId):
    game = Games.query.filter_by(id=gameId).first()
    if not game:
        abort(404)
    game = game.__dict__
    del game["_sa_instance_state"]
    return json.dumps(game, ensure_ascii=False, default=str)

@app.route("/gameFile/<id>")
def gameFile(id):
    if id != None:
        game = Games.query.filter_by(id=id).first()
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


@app.route("/searchMovies/<library>/<user>/<search>")
def searchMovies(library, user, search):
    search = search.replace("%20", " ").lower()
    search_terms = search.split()

    movies = Movies.query.filter_by(libraryName=library).all()
    results = {}
    for movie in movies:
        count = 0
        title = movie.title.lower()
        real_title = movie.realTitle.lower()
        slug = movie.slug.lower()
        description = movie.description.lower().split(" ")
        cast = movie.cast.lower()
        date = str(movie.date).lower()
        genre = movie.genre.lower()
        alternatives_names = movie.alternativesNames.lower()
        valueUsed = [title, real_title, slug, cast, date, genre, alternatives_names]
        for term in search_terms:
            for value in valueUsed:
                if term in value:
                    count += 1
            for word in description:
                if term == word.lower():
                    count += 1
        if count > 0:
            results[movie] = count
    
    results = sorted(results.items(), key=lambda x: x[1], reverse=True)

    movies = [i[0].__dict__ for i in results]
    for i in movies:
        del i["_sa_instance_state"]

    theUser = Users.query.filter_by(name=user).first()
    userType = theUser.accountType

    if userType in ["Kid", "Teen"]:
        for movie in movies:
            if movie["adult"] == "True":
                movies.remove(movie)
    return json.dumps(movies, ensure_ascii=False)


@app.route("/searchSeries/<library>/<user>/<search>")
def searchSeries(library, user, search):
    search = unidecode(search.replace("%20", " ").lower())
    search_terms = search.split()

    series = Series.query.filter_by(libraryName=library).all()

    results = []
    
    for serie in series:
        count = 0
        name = unidecode(serie.name.lower())
        original_name = unidecode(serie.originalName.lower())
        description = unidecode(serie.description.lower())
        cast = unidecode(serie.cast.lower())
        date = unidecode(str(serie.date).lower())
        genre = unidecode(serie.genre.lower())

        valueUsed = [name, original_name, description, cast, date, genre]

        for term in search_terms:
            for value in valueUsed:
                if term in value:
                    count += 1
            for word in description:
                if term == word.lower():
                    count += 1
        if count > 0:
            results.append(serie)


    results = sorted(results.items(), key=lambda x: x[1], reverse=True)

    series = [i.__dict__ for i in results]
    for serie in series:
        del serie["_sa_instance_state"]

    user = Users.query.filter_by(name=user).first()
    userType = user.accountType
    
    if userType in ["Kid", "Teen"]:
        for serie in series:
            if serie["adult"] == "True":
                series.remove(serie)
    return json.dumps(series, ensure_ascii=False)

@app.route("/searchBooks/<library>/<user>/<search>")
def searchBooks(library, user, search):
    search = unidecode(search.replace("%20", " ").lower())
    search_terms = search.split()

    books = Books.query.filter_by(libraryName=library).all()

    results = []

    for book in books:
        count = 0
        title = unidecode(book.title.lower())
        slug = unidecode(book.slug.lower())
        bookType = unidecode(book.bookType.lower())
        cover = unidecode(book.cover.lower())

        valueUsed = [title, slug, bookType, cover]

        for term in search_terms:
            for value in valueUsed:
                if term in value:
                    count += 1
        if count > 0:
            results.append(book)


    books = [i.__dict__ for i in results]
    for book in books:
        del book["_sa_instance_state"]

    user = Users.query.filter_by(name=user).first()
    userType = user.accountType
    
    if userType in ["Kid", "Teen"]:
        for book in books:
            if book["adult"] == "True":
                books.remove(book)
    #reorder by title
    books = sorted(books, key=lambda k: k['title'])
    return json.dumps(books, ensure_ascii=False)


@app.route("/searchOthers/<library>/<user>/<search>")
def searchOthers(library, user, search):
    search = search.replace("%20", " ").lower()
    search_terms = search.split()

    others = OthersVideos.query.filter_by(libraryName=library).all()
    results = {}
    for other in others:
        count = 0
        videoHash = other.videoHash.lower()
        title = other.title.lower()
        slug = other.slug.lower()

        valueUsed = [title, slug, videoHash]
        for term in search_terms:
            for value in valueUsed:
                if term in value:
                    count += 1
        if count > 0:
            results[movie] = count
    
    results = sorted(results.items(), key=lambda x: x[1], reverse=True)

    movies = [i[0].__dict__ for i in results]
    for i in movies:
        del i["_sa_instance_state"]

    theUser = Users.query.filter_by(name=user).first()
    userType = theUser.accountType

    if userType in ["Kid", "Teen"]:
        for movie in movies:
            if movie["adult"] == "True":
                movies.remove(movie)
    return json.dumps(movies, ensure_ascii=False)

@app.route("/setVuesTimeCode/", methods=["POST"])
def setVuesTimeCode():
    data = request.get_json()
    movieID = data["movieID"]
    timeCode = data["timeCode"]
    username = data["username"]
    movie = Movies.query.filter_by(id=movieID).first()
    if movie is None:
        abort(404)

    actualVues = movie.vues
    p = re.compile('(?<!\\\\)\'')
    actualVues = p.sub('\"', actualVues)
    actualVues = json.loads(actualVues)
    actualVues[username] = timeCode
    actualVues = str(actualVues).replace("'", '"')
    movie.vues = actualVues
    db.session.commit()
    return "ok"

@app.route("/setVuesOtherTimeCode/", methods=["POST"])
def setVuesOtherTimeCode():
    data = request.get_json()
    videoHash = data["movieHASH"]
    timeCode = data["timeCode"]
    username = data["username"]
    video = OthersVideos.query.filter_by(videoHash=videoHash).first()
    if video is None:
        abort(404)

    actualVues = video.vues
    p = re.compile('(?<!\\\\)\'')
    actualVues = p.sub('\"', actualVues)
    actualVues = json.loads(actualVues)
    actualVues[username] = timeCode
    actualVues = str(actualVues).replace("'", '"')
    video.vues = actualVues
    db.session.commit()
    return "ok"

@app.route("/whoami", methods=["POST"])
def whoami():
    data = request.get_json()
    user_id = data["user_id"]

    if user_id is None:
        return jsonify({"error": "not logged in"})

    user = Users.query.filter_by(id=user_id).first()

    return jsonify({"id":user_id, "user": user.name})
    
@app.route("/mainMovie/<movieID>")
def mainMovie(movieID):
    movie = Movies.query.filter_by(id=movieID).first()
    slug = movie.slug
    library = movie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    video_path = f"{path}/{slug}"
    videoProperties = get_video_properties(video_path)
    height = int(videoProperties["height"])
    width = int(videoProperties["width"])
    m3u8File = f"""#EXTM3U\n\n"""
    #m3u8File += generateAudioMovie(movieID)
    qualities = [144, 240, 360, 480, 720, 1080]
    file = []
    for quality in qualities:
        if quality < height:
            newWidth = int(quality)
            newHeight = int(float(width) / float(height) * newWidth)
            if (newHeight % 2) != 0:
                newHeight += 1
            m3u8Line = f"""#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH={newWidth*newHeight},CODECS=\"avc1.4d4033,mp4a.40.2",AUDIO="audio",RESOLUTION={newHeight}x{newWidth}\n/video/{quality}/{movieID}.m3u8\n"""
            file.append(m3u8Line)
    lastLine = f"""#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH={width*height},CODECS=\"avc1.4d4033,mp4a.40.2",AUDIO="audio",RESOLUTION={width}x{height}\n/video/{movieID}.m3u8\n\n\n"""
    file.append(lastLine)
    file = "".join(file)
    m3u8File += file
    response = make_response(m3u8File)

    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set("Content-Disposition", "attachment", filename=f"{movieID}.m3u8")
    return response

@app.route("/movieAmbient/<movieID>")
def movieAmbient(movieID):
    movie = Movies.query.filter_by(id=movieID).first()
    lib = movie.libraryName
    theLib = Libraries.query.filter_by(libName=lib).first()
    path = theLib.libFolder
    if movie is None:
        abort(404)
    video_path = movie.slug
    video_path = f"{path}/{video_path}"

    frames = []
    return jsonify(frames)

@app.route("/mainSerie/<episodeID>")
def mainSerie(episodeID):
    episode = Episodes.query.filter_by(episodeId=episodeID).first()
    season = Seasons.query.filter_by(seasonId=episode.seasonId).first()
    serie = Series.query.filter_by(id=season.serie).first()
    library = serie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    episodePath = episode.slug
    episodePath = episodePath.replace("\\", "/")
    episodePath = f"{path}{episodePath}"

    videoProperties = get_video_properties(episodePath)
    height = int(videoProperties["height"])
    width = int(videoProperties["width"])
    m3u8File = f"""#EXTM3U\n\n"""
    file = []
    qualities = [144, 240, 360, 480, 720, 1080]
    for quality in qualities:
        if quality < height:
            newWidth = int(quality)
            newHeight = int(float(width) / float(height) * newWidth)
            if (newHeight % 2) != 0:
                newHeight += 1
            m3u8Line = f"""#EXT-X-STREAM-INF:BANDWIDTH={newWidth*newWidth},RESOLUTION={newHeight}x{newWidth}\n/videoSerie/{quality}/{episodeID}\n"""
            file.append(m3u8Line)
    lastLine = f'#EXT-X-STREAM-INF:BANDWIDTH={width*height},RESOLUTION={width}x{height}\n/videoSerie/{episodeID}\n'
    file.append(lastLine)
    file = file[::-1]
    file = "".join(file)
    m3u8File += file

    response = make_response(m3u8File)

    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{episodeID}.m3u8"
    )
    return response


@app.route("/mainOther/<otherHash>")
def mainOther(otherHash):
    movie = OthersVideos.query.filter_by(videoHash=otherHash).first()
    video_path = movie.slug
    videoProperties = get_video_properties(video_path)
    height = int(videoProperties["height"])
    width = int(videoProperties["width"])
    m3u8File = f"""#EXTM3U\n\n"""
    qualities = [144, 240, 360, 480, 720, 1080]
    file = []
    for quality in qualities:
        if quality < height:
            newWidth = int(quality)
            newHeight = int(float(width) / float(height) * newWidth)
            if (newHeight % 2) != 0:
                newHeight += 1
            m3u8Line = f"""#EXT-X-STREAM-INF:BANDWIDTH={newWidth*newWidth},RESOLUTION={newHeight}x{newWidth}\n/other-video/{quality}/{otherHash}\n"""
            file.append(m3u8Line)
    lastLine = f'#EXT-X-STREAM-INF:BANDWIDTH={width*height},RESOLUTION={width}x{height}"\n/other-video/{otherHash}\n'
    file.append(lastLine)
    file = file[::-1]
    file = "".join(file)
    m3u8File += file
    response = make_response(m3u8File)

    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{otherHash}.m3u8"
    )
    return response

def generateCaptionSerie(episodeId):
    episode = Episodes.query.filter_by(episodeId=episodeId).first()
    season = Seasons.query.filter_by(seasonId=episode.seasonId).first()
    serie = Series.query.filter_by(id=season.serie).first()
    library = serie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    episodePath = episode.slug
    episodePath = episodePath.replace("\\", "/")
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

    captionResponse.pop()

    for line in captionResponse:
        line = line.rstrip()
        language = line.split(",")[1]
        newLanguage = pycountry.languages.get(alpha_2=language)
        index = line.split(",")[0]
        try:
            title = line.split(",")[2]

            try:
                titleName = title.split(" : ")[0]
                subtitleType = title.split(" : ")[1]
            except:
                titleName = title
                subtitleType = "Unknown"

        except:
            titleName = newLanguage
            subtitleType = "Unknown"
        if subtitleType.lower() != "pgs":
            allCaptions.append(
                {
                    "index": index,         "languageCode": language,         "language": newLanguage,         "url": f"/chunkCaptionSerie/{language}/{index}/{episodeId}.vtt",         "name": titleName,     }
            )
    return allCaptions

def generateCaptionMovie(movieID):
    movie = Movies.query.filter_by(id=movieID).first()
    library = movie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    moviePath = movie.slug
    moviePath = moviePath.replace("\\", "/")
    slug = f"{path}\{moviePath}"

    captionCommand = [
        "ffprobe",
        "-loglevel",
        "error",
        "-select_streams",
        "s",
        "-show_entries",
        "stream=index:stream_tags=language,title",
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
    captionResponse.pop()
    allCaptions = []
    for line in captionResponse:
        line = line.rstrip()
        language = line.split(",")[1]
        try:
            newLanguage = pycountry.languages.get(alpha_2=language).name
        except:
            try:
                newLanguage = pycountry.languages.get(alpha_3=language).name
            except:
                newLanguage = language
        index = line.split(",")[0]
        titleName = line.split(",")[2]
        if titleName.lower() == "full":
            titleName = f"{newLanguage} Full"
        allCaptions.append(
            {
                "index": index,     "languageCode": language,     "language": newLanguage,     "url": f"/chunkCaption/vtt/{index}/{movieID}.vtt",     "name": titleName, }
        )

    return allCaptions

def generateAudioMovie(movieID):
    moviePath = Movies.query.filter_by(id=movieID).first().slug
    library = Movies.query.filter_by(id=movieID).first().libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    moviePath = moviePath.replace("\\", "/")
    slug = f"{path}\{moviePath}"
    command = [
        "ffprobe",
        "-loglevel",
        "error",
        "-select_streams",
        "a",
        "-show_entries",
        "stream=index:stream_tags=language:stream_tags=title",
        "-of",
        "csv=p=0",
        slug,
    ]
    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)
    response = pipe.stdout.read().decode("utf-8")
    response = response.split("\n")
    response.pop()
    allTracks = []
    for line in response:
        line = line.rstrip()
        language = line.split(",")[1].upper()
        index = line.split(",")[0]
        try:
            title = line.split(",")[2]
            if " " in title:
                title = language
        except:
            title = language
        default = "YES" if index == "1" else "NO"
        default = "NO"
        theTrack = f"#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID=\"audio\",NAME=\"{title.capitalize()}\",LANGUAGE=\"{language.lower()}\",AUTOSELECT=YES,DEFAULT={default},URI=\"/audioMovie/{movieID}/{index}\""
        allTracks.append(theTrack)
    #convert allTracks to a multi-line string
    allTracksString = ""
    for track in allTracks:
        allTracksString += f"{track}\n"
    allTracksString += "\n"
    return allTracksString

def generateAudioSerie(episodeID):
    episode = Episodes.query.filter_by(episodeId=episodeID).first()
    season = Seasons.query.filter_by(seasonId=episode.seasonId).first()
    serie = Series.query.filter_by(id=season.serie).first()
    library = serie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    episodePath = episode.slug
    episodePath = episodePath.replace("\\", "/")
    slug = f"{path}{episodePath}"
    #get the stream map
    command = [
        "ffprobe",
        "-loglevel",
        "error",
        "-select_streams",
        "a",
        "-show_entries",
        "stream=index:stream_tags=language:stream_tags=title:stream_tags=handler_name:stream_tags=handler",
        "-of",
        "csv=p=0",
        slug,
    ]
    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)
    response = pipe.stdout.read().decode("utf-8")
    response = response.split("\n")
    response.pop()
    allTracks = []
    for line in response:
        line = line.rstrip()
        index = line.split(",")[0]
        language = line.split(",")[1].upper()
        default = "YES" if index == "1" else "NO"
        theTrack = f"#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID=\"SERIEAUDIO\",NAME=\"{language}\",LANGUAGE=\"{language}\",AUTOSELECT={default},DEFAULT={default},URI=\"/audioSeries/{episodeID}/{index}\""
        allTracks.append(theTrack)
        
    allTracksString = ""
    for track in allTracks:
        allTracksString += f"{track}\n"
    return allTracksString

@app.route("/audioMovie/<movieId>/<trackId>")
def audioMovie(trackId, movieId):
    movie = Movies.query.filter_by(id=movieId).first()
    library = movie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    moviePath = movie.slug
    moviePath = moviePath.replace("\\", "/")
    slug = f"{path}\{moviePath}"
    duration = length_video(slug)

    file = f"""#EXTM3U
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-TARGETDURATION:{CHUNK_LENGTH}
    """

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""
#EXTINF:{int(CHUNK_LENGTH)},
/chunkAudio/{movieId}/{trackId}-{(i // CHUNK_LENGTH) + 1}.ts"""

    file += """
    
#EXT-X-ENDLIST
"""

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{trackId}.m3u8"
    )
    return response

@app.route("/audioSeries/<episodeId>/<trackId>")
def audioSeries(trackId, episodeId):
    episode = Episodes.query.filter_by(episodeId=episodeId).first()
    season = Seasons.query.filter_by(seasonId=episode.seasonId).first()
    serie = Series.query.filter_by(id=season.serie).first()
    library = serie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    episodePath = episode.slug
    episodePath = episodePath.replace("\\", "/")
    slug = f"{path}{episodePath}"
    duration = length_video(slug)

    file = f"""
#EXTM3U
#EXT-X-VERSION:4
#EXT-X-TARGETDURATION:{CHUNK_LENGTH}
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-PLAYLIST-TYPE:VOD
    """

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""
#EXTINF:{float(CHUNK_LENGTH)},
/chunkAudioSerie/{episodeId}/{trackId}-{(i // CHUNK_LENGTH) + 1}
        """

    file += """
#EXT-X-ENDLIST"""

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{trackId}.m3u8"
    )
    return response
        
@app.route("/chunkAudio/<movieId>/<trackId>-<int:chunkIndex>.ts", methods=["GET"])
def chunkAudio(movieId, trackId, chunkIndex):
    seconds = (chunkIndex-1) * CHUNK_LENGTH
    movie = Movies.query.filter_by(id=movieId).first()
    slug = movie.slug
    library = movie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    video_path = f"{path}/{slug}"
    end = chunkIndex-1
    if end < 10:
        end = "0"+str(end)
    end2 = chunkIndex
    if end2 < 10:
        end2 = "0"+str(end2)
        
    time_start = "0"+str(datetime.timedelta(seconds=seconds))+"."+str(end)
    time_end = "0"+str(datetime.timedelta(seconds=seconds + CHUNK_LENGTH))+"."+str(end2)
    logLevelValue = "error"
    command = [
        "ffmpeg",
        "-loglevel",
        logLevelValue,
        "-ss",
        time_start,
        "-i",
        video_path,
        "-to",
        time_end,
        "-c:a",
        "aac",
        "-vn",
        "-ac",
        "4",
        "-map",
        f"0:{trackId}",
        "-f",
        "adts",
        "pipe:1",
    ]
    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{trackId}-{chunkIndex}.ts"
    )


    return response

@app.route("/chunkAudioSerie/<episodeId>/<trackId>-<int:chunkIndex>", methods=["GET"])
def chunkAudioSerie(episodeId, trackId, chunkIndex):
    seconds = (chunkIndex - 1) * CHUNK_LENGTH
    episode = Episodes.query.filter_by(episodeId=episodeId).first()
    season = Seasons.query.filter_by(seasonId=episode.seasonId).first()
    serie = Series.query.filter_by(id=season.serie).first()
    slug = episode.slug
    library = serie.libraryName
    theLibrary = Libraries.query.filter_by(libName=library).first()
    path = theLibrary.libFolder
    video_path = f"{path}/{slug}"
    time_start = str(datetime.timedelta(seconds=seconds))
    time_end = str(datetime.timedelta(seconds=seconds + CHUNK_LENGTH))
    logLevelValue = "error"
    command = [
        "ffmpeg",
        "-loglevel",
        logLevelValue,
        "-ss",
        time_start,
        "-to",
        time_end,
        "-i",
        video_path,
        "-c:a",
        "aac",
        "-vn",
        "-ac",
        "2",
        "-b:a",
        "196k",
        "-map",
        f"0:{trackId}",
        "-f",
        "adts",
        "-",
    ]
    
    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{trackId}-{chunkIndex}.aac"
    )

    return response

@app.route("/getActorData/<actorId>", methods=["GET", "POST"])
def getActorData(actorId):
    if actorId == "undefined":
        abort(404)
    moviesData = []
    seriesData = []
    actor = Actors.query.filter_by(actorId=actorId).first()
    movies = actor.actorPrograms.split(" ")
    for movie in movies:
        inMovies = Movies.query.filter_by(id=movie).first() is not None
        inSeries = Series.query.filter_by(id=movie).first() is not None
        if inMovies:
            thisMovie = Movies.query.filter_by(id=movie).first().__dict__
            del thisMovie["_sa_instance_state"]
            if thisMovie not in moviesData:
                moviesData.append(thisMovie)
        elif inSeries:
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
    return jsonify({"isChocolate": True})

@app.route("/downloadMovie/<movieId>")
def downloadMovie(movieId):
    config = configparser.ConfigParser()
    config.read(os.path.join(dir, 'config.ini'))
    canDownload = config["ChocolateSettings"]["allowDownload"].lower() == "true"
    if False:
        return jsonify({"error": "download not allowed"})
    movie = Movies.query.filter_by(id=movieId).first()
    moviePath = movie.slug
    movieLibrary = movie.libraryName
    library = Libraries.query.filter_by(libName=movieLibrary).first()
    libraryPath = library.libFolder
    moviePath = f"{libraryPath}/{moviePath}"
    return send_file(moviePath, as_attachment=True)

@app.route("/downloadEpisode/<episodeId>")
def downloadEpisode(episodeId):
    config = configparser.ConfigParser()
    config.read(os.path.join(dir, 'config.ini'))
    canDownload = config["ChocolateSettings"]["allowDownload"].lower() == "true"
    if not canDownload:
        return jsonify({"error": "download not allowed"})
    episode = Episodes.query.filter_by(episodeId=episodeId).first()
    season = Seasons.query.filter_by(seasonId=episode.seasonId).first()
    serie = Series.query.filter_by(id=season.serie).first()
    library = Libraries.query.filter_by(libName=serie.libraryName).first()
    libraryPath = library.libFolder
    episodePath = f"{libraryPath}/{episode.slug}"
    return send_file(episodePath, as_attachment=True)
       

if __name__ == "__main__":
    enabledRPC = config["ChocolateSettings"]["discordrpc"]
    if enabledRPC == "true":
        try:
            RPC.update(
            state="Loading Chocolate...", details=f"The Universal MediaManager | v{chocolateVersion} ({lastCommitHash})", large_image="loader", large_text="Chocolate", buttons=[{"label": "Github", "url": "https://github.com/ChocolateApp/Chocolate"}], start=start_time)
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
            elif library["libType"] == "other":
                getOthersVideos(library["libName"])
            elif library["libType"] == "books":
                getBooks(library["libName"])

    print()
    print("\033[?25h", end="")
    
    enabledRPC = config["ChocolateSettings"]["discordrpc"]
    if enabledRPC == "true":
        try:
            RPC.update(
            state="Idling", details=f"The Universal MediaManager | v{chocolateVersion} ({lastCommitHash})", large_image="largeimage", large_text="Chocolate", buttons=[{"label": "Github", "url": "https://github.com/ChocolateApp/Chocolate"}], start=time())
        except:
            pass

    with app.app_context():
        allSeriesDict = {}
        for u in db.session.query(Series).all():
            allSeriesDict[u.name] = u.__dict__
       
    app.run(host="0.0.0.0", port="8888")