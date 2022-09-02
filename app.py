from flask import Flask, url_for, request, render_template, redirect, make_response
from flask_cors import CORS
from tmdbv3api import TMDb, Movie, TV, Episode, Person
from tmdbv3api.exceptions import TMDbException
from videoprops import get_video_properties, get_audio_properties
from bs4 import BeautifulSoup
from pathlib import Path
import requests, os, subprocess, configparser, socket, datetime, subprocess, socket, platform, GPUtil, json, random
from Levenshtein import distance as lev
from fuzzywuzzy import fuzz
from ask_lib import AskResult, ask

app = Flask(__name__)
CORS(app)

tmdb = TMDb()
tmdb.api_key = 'cb862a91645ec50312cf636826e5ca1f'

config = configparser.ConfigParser()
config.read('config.ini')

if config["ChocolateSettings"]["language"] == "Empty":
    config["ChocolateSettings"]["language"] = "en-US"

tmdb.language = config["ChocolateSettings"]["language"]
tmdb.debug = True
movie = Movie()
show = TV()

searchedFilms = []
simpleDataFilms = []
allMoviesNotSorted = []
allMoviesDict = {}

searchedSeries = []
simpleDataSeries = {}
allSeriesNotSorted = []
allSeriesDict = {}
allSeriesDictTemp = {}
currentCWD = os.getcwd()

with open(f"{currentCWD}/scannedFiles.json", 'r', encoding="utf8") as f:
    jsonFileToRead = json.load(f)

hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
config.set("ChocolateSettings", "localIP", local_ip)
serverPort = config["ChocolateSettings"]["port"]

filmEncode = None
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
movieExtension = ""
websitesTrailers = {"YouTube": "https://www.youtube.com/embed/", "Dailymotion": "https://www.dailymotion.com/video/", "Vimeo": "https://vimeo.com/"}

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
            originalMovieTitle = movieTitle
            size = len(movieTitle)
            movieTitle, extension = os.path.splitext(movieTitle)
            try:
                search = movie.search(movieTitle)
            except TMDbException:
                print(TMDbException)
                allMoviesNotSorted.append(search)
                continue
                
            if not search:
                allMoviesNotSorted.append(originalMovieTitle)
                continue
            index = filmFileList.index(searchedFilm)+1
            percentage = index*100/len(filmFileList)


            loadingFirstPart = ("•"*int(percentage*0.2))[:-1]
            loadingFirstPart = loadingFirstPart+"➤"
            loadingSecondPart = ("•"*(20-int(percentage*0.2)))
            loading = f"{str(int(percentage)).rjust(3)}% | [\33[32m{loadingFirstPart} \33[31m{loadingSecondPart}\33[0m] | {movieTitle} | {index}/{len(filmFileList)}                                                      "
            print('\033[?25l', end="")
            print(loading, end='\r', flush=True)
            
            bestMatch = search[0]
            for i in range(len(search)):
                if lev(movieTitle, search[i].title) < lev(movieTitle, bestMatch.title) and bestMatch.title not in filmFileList:
                    bestMatch = search[i]
                elif lev(movieTitle, search[i].title) == lev(movieTitle, bestMatch.title) and bestMatch.title not in filmFileList:
                    bestMatch = bestMatch
                if lev(movieTitle, bestMatch.title) == 0 and bestMatch.title not in filmFileList:
                    break
            
            res = bestMatch
            name = res.title

            with open(f"{currentCWD}/scannedFiles.json", 'r', encoding="utf8") as f:
                jsonFileToRead = json.load(f)
            if name not in jsonFileToRead["movies"]:
                movieCoverPath = f"https://image.tmdb.org/t/p/original{res.poster_path}"
                banniere = f"https://image.tmdb.org/t/p/original{res.backdrop_path}"
                rewritedName = movieTitle.replace(" ", "_")
                if not os.path.exists(f"{currentCWD}/static/img/mediaImages/{rewritedName}_Cover.png"):
                    with open(f"{currentCWD}/static/img/mediaImages/{rewritedName}_Cover.png", 'wb') as f:
                        f.write(requests.get(movieCoverPath).content)
                if not os.path.exists(f"{currentCWD}/static/img/mediaImages/{rewritedName}_Banner.png"):
                    with open(f"{currentCWD}/static/img/mediaImages/{rewritedName}_Banner.png", 'wb') as f:
                        f.write(requests.get(banniere).content)
                banniere = f"/static/img/mediaImages/{rewritedName}_Banner.png"
                movieCoverPath = f"/static/img/mediaImages/{rewritedName}_Cover.png"
                
                size1 = os.path.getsize(f"{currentCWD}{movieCoverPath}")
                size2 = os.path.getsize(f"{currentCWD}{banniere}")
                if size1 < 10240:
                    movieCoverPath = "/static/img/broken.png"
                if size2 < 10240:
                    banniere = "/static/img/brokenBanner.png"
                description = res.overview
                note = res.vote_average
                date = res.release_date
                movieId = res.id
                details = movie.details(movieId)

                casts = details.casts.cast
                theCast = []
                for cast in casts:
                    while len(theCast) < 5:
                        characterName = cast.character
                        actorName = cast.name.replace(" ", "_").replace("/", "").replace(" \"", "")
                        imagePath = f"https://www.themoviedb.org/t/p/w600_and_h900_bestv2{cast.profile_path}"
                        if not os.path.exists(f"{currentCWD}/static/img/mediaImages/Actor_{actorName}.png"):
                            with open(f"{currentCWD}/static/img/mediaImages/Actor_{actorName}.png", 'wb') as f:
                                f.write(requests.get(imagePath).content)
                        imagePath = f"/static/img/mediaImages/Actor_{actorName}.png"
                        actor = [cast.name, characterName , imagePath]
                        if actor not in theCast:
                            theCast.append(actor)
                        else:
                            break
                try:
                    date = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y")
                except ValueError as e:
                    print(e)
                    date = "Unknown"

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
                    if int(seconds) < 10:
                        seconds = f"0{seconds}"
                    length = f"{minutes}:{seconds}"
                elif len(length) == 1:
                    seconds = str(round(float(length[0])))
                    if int(seconds) < 10:
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

                bandeAnnonce = details.videos.results
                if len(bandeAnnonce) > 0:
                    for video in bandeAnnonce:
                        bandeAnnonceType = video.type
                        bandeAnnonceHost = video.site
                        bandeAnnonceKey = video.key
                        if bandeAnnonceType == "Trailer":
                            try:
                                bandeAnnonceUrl = websitesTrailers[bandeAnnonceHost] + bandeAnnonceKey
                                break
                            except KeyError as e:
                                bandeAnnonceUrl = "Unknown"
                                print(e)


                filmData = {
                    "title": movieTitle,
                    "realTitle": name,
                    "cover": movieCoverPath,
                    "banner": banniere,
                    "slug": originalMovieTitle,
                    "description": description,
                    "note": note,
                    "date": date,
                    "genre": movieGenre,
                    "duration": str(duration),
                    "id": movieId,
                    "cast": theCast,
                    "bandeAnnonce": bandeAnnonceUrl,
                }

                searchedFilms.append(filmData)
                simpleFilmData = {
                    "title": movieTitle,
                    "realTitle": name,
                    "cover": movieCoverPath,
                    "banner": banniere,
                    "genre": movieGenre,
                    "description": description,
                    "slug": originalMovieTitle,
                }
                simpleDataFilms.append(simpleFilmData)
                allMoviesDict[name] = filmData
                jsonData = filmData

                with open(f"{currentCWD}/scannedFiles.json", 'r', encoding="utf8") as f:
                    jsonFile = json.load(f)
                    jsonFile["movies"][name] = jsonData
                with open(f"{currentCWD}/scannedFiles.json", "w", encoding="utf8") as f:
                    json.dump(jsonFile, f, ensure_ascii=False)

            else:
                with open(f"{currentCWD}/scannedFiles.json", 'r', encoding="utf8") as f:
                    jsonFileToRead = json.load(f)
                data = jsonFileToRead["movies"]
                data = data[name]
                filmData = {
                    "title": data["title"],
                    "realTitle": data["realTitle"],
                    "cover": data["cover"],
                    "banner": data["banner"],
                    "slug": data["slug"],
                    "description": data["description"],
                    "note": data["note"],
                    "date": data["date"],
                    "genre": data["genre"],
                    "duration": data["duration"],
                    "id": data["id"],
                    "cast": data["cast"],
                    "bandeAnnonce": data["bandeAnnonce"],
                }

                searchedFilms.append(filmData)
                simpleFilmData = {
                    "title": data["title"],
                    "realTitle": data["realTitle"],
                    "cover": data["cover"],
                    "banner": data["banner"],
                    "slug": data["slug"],
                    "description": data["description"],
                    "genre": data["genre"],
                }
                simpleDataFilms.append(simpleFilmData)
                allMoviesDict[name] = filmData
        elif searchedFilm.endswith("/") == False :
            allMoviesNotSorted.append(searchedFilm)
    allMoviesJson = jsonFileToRead["movies"]
    for movie in allMoviesJson:
        name = movie
        slug = allMoviesJson[movie]["slug"]
        movies = os.listdir(path)
        if slug not in movies:
            with open(f"{currentCWD}/scannedFiles.json", 'r', encoding="utf8") as f:
                jsonFile = json.load(f)
                del jsonFile["movies"][name]
            with open(f"{currentCWD}/scannedFiles.json", "w", encoding="utf8") as f:
                json.dump(jsonFile, f, ensure_ascii=False)
    print()

def getSeries():
    print("SerieServer is starting")
    try:
        if config["ChocolateSettings"]["SeriesPath"] == "Empty":
            allSeriesPath = str(Path.home() / "Downloads")
        else:
            allSeriesPath = os.path.normpath(config["ChocolateSettings"]["SeriesPath"])
    except KeyError as e:
        print(e)
        allSeriesPath = str(Path.home() / "Downloads")
    if allSeriesPath == ".":
        allSeriesPath = str(Path.home() / "Downloads")
    try:
        allSeries = [ name for name in os.listdir(allSeriesPath) if os.path.isdir(os.path.join(allSeriesPath, name)) and name.endswith((".rar", ".zip", ".part")) == False ]
    except OSError as e:
        print("No series found")
        print(e)
        return

    allSeasonsAppelations = ["S"]
    allEpisodesAppelations = ["E"]
    for series in allSeries:
        uglySeasonAppelations= ["Saison", "Season", series.replace(" ", ".")]
        seasons = os.listdir(f"{allSeriesPath}\\{series}")
        serieSeasons = {}
        for season in seasons:
            path = f"{allSeriesPath}/{series}"
            if not (season.startswith(tuple(allSeasonsAppelations)) and not season.endswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9"))) or season.startswith(tuple(uglySeasonAppelations)):
                allSeasons = os.listdir(f"{path}")
                for allSeason in allSeasons:
                    untouchedSeries = config["ChocolateSettings"]["untouchedSeries"].split(";")
                    if (allSeriesPath != str(Path.home() / "Downloads") or allSeriesPath != ".") and allSeason not in untouchedSeries and (allSeason.startswith(tuple(allSeasonsAppelations)) == False and allSeason.endswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")) == False) or season.startswith(tuple(uglySeasonAppelations)):
                        if os.path.isdir(f"{path}/{allSeason}") and not (season.startswith(tuple(allSeasonsAppelations)) and not season.endswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9"))):
                            print(f"For {uglySeasonAppelations[2]} : {allSeason}")
                            reponse = ask(f"I found that folder, can I rename it from {allSeason} to S{allSeasons.index(allSeason)+1}", AskResult.YES)
                            if reponse:
                                try:
                                    os.rename(f"{path}/{allSeason}", f"{path}/S{allSeasons.index(allSeason)+1}")
                                except Exception as e:
                                    print(f"Something went wrong : {e}")
                            else:
                                if config["ChocolateSettings"]["untouchedSeries"] == "Empty":
                                    config.set("ChocolateSettings", "untouchedSeries", allSeason)
                                else:
                                    untouchedSeries = config["ChocolateSettings"]["untouchedSeries"]
                                    config.set("ChocolateSettings", "untouchedSeries", f"{untouchedSeries};{allSeason}")
                                with open(f'{currentCWD}/config.ini', 'w') as conf:
                                    config.write(conf)

            
            episodesPath = f"{path}\{season}"
            try:
                seasonNumber = season.split(" ")[1]
            except Exception as e:
                seasonNumber = season[1:]
            if os.path.isdir(episodesPath):
                episodes = os.listdir(episodesPath)
                seasonEpisodes = {}
                oldIndex = 0
                for episode in episodes:
                    episodeName, episodeExtension = os.path.splitext(episode)
                    if os.path.isfile(f"{episodesPath}/{episode}"):
                        if episodeName.startswith(tuple(allEpisodesAppelations)) and episodeName.endswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")):
                            oldIndex = episodes.index(episode)
                        else:
                            actualName = f"{episodesPath}/{episode}"
                            oldIndex = episodes.index(episode)
                            try:
                                os.rename(actualName, f"{episodesPath}/E{episodes.index(episode)+1}{episodeExtension}")
                            except FileExistsError as e:
                                print(f"Problème de rename avec {actualName}\n{e}")
                            episode = f"E{oldIndex+1}{episodeExtension}"
                        seasonEpisodes[oldIndex+1] = f"{path}/{season}/{episode}"
                serieSeasons[seasonNumber] = seasonEpisodes
        serieData = {}
        serieData["seasons"] = serieSeasons
        allSeriesDictTemp[series] = serieData
        

    allSeries = allSeriesDictTemp
    allSeriesName = []
    for series in allSeries:
        allSeriesName.append(series)
        for season in allSeries[series]["seasons"]:
            for episode in allSeries[series]["seasons"][season]:
                actualPath = allSeries[series]["seasons"][season][episode]
                HTTPPath = actualPath.replace(allSeriesPath, "http://localhost:8800")
                HTTPPath = HTTPPath.replace("\\", "/")

    for serie in allSeriesName:
        if not isinstance(serie, str):
            print(f"{serie} is not 'isinstance'")
            continue
        show = TV()
        serieTitle = serie
        originalSerieTitle = serieTitle

        try:
            search = show.search(serieTitle)
        except TMDbException as e:
            print(e)
            allSeriesNotSorted.append(serieTitle)
            break
                    
        if not search:
            allSeriesNotSorted.append(serieTitle)
            print(f"{originalSerieTitle} return nothing, try to rename it, the english name return more results.")
            continue
        index = allSeriesName.index(serieTitle)+1
        percentage = index*100/len(allSeriesName)

        loadingFirstPart = ("•"*int(percentage*0.2))[:-1]
        loadingFirstPart = loadingFirstPart+"➤"
        loadingSecondPart = ("•"*(20-int(percentage*0.2)))
        loading = f"{str(int(percentage)).rjust(3)}% | [\33[32m{loadingFirstPart} \33[31m{loadingSecondPart}\33[0m] | {serieTitle} | {index}/{len(allSeriesName)}                              "
        print('\033[?25l', end="")
        print(loading, end='\r', flush=True)

        bestMatch = search[0]
        for i in range(len(search)):
            if lev(serieTitle, search[i].name) < lev(serieTitle, bestMatch.name) and bestMatch.name not in allSeriesName:
                bestMatch = search[i]
            elif lev(serieTitle, search[i].name) == lev(serieTitle, bestMatch.name) and bestMatch.name not in allSeriesName:
                bestMatch = bestMatch
            if lev(serieTitle, bestMatch.name) == 0 and bestMatch.name not in allSeriesName:
                break
                
        
        res = bestMatch
        name = res.name
        with open(f"{currentCWD}/scannedFiles.json", 'r', encoding="utf8") as f:
            jsonFileToRead = json.load(f)
        if name not in jsonFileToRead["series"]:
            serieCoverPath = f"https://image.tmdb.org/t/p/original{res.poster_path}"
            banniere = f"https://image.tmdb.org/t/p/original{res.backdrop_path}"
            rewritedName = originalSerieTitle.replace(" ", "_")
            if not os.path.exists(f"{currentCWD}/static/img/mediaImages/{rewritedName}_Cover.png"):
                with open(f"{currentCWD}/static/img/mediaImages/{rewritedName}_Cover.png", 'wb') as f:
                    f.write(requests.get(serieCoverPath).content)
            if not os.path.exists(f"{currentCWD}/static/img/mediaImages/{rewritedName}_Banner.png"):
                with open(f"{currentCWD}/static/img/mediaImages/{rewritedName}_Banner.png", 'wb') as f:
                    f.write(requests.get(banniere).content)
            banniere = f"/static/img/mediaImages/{rewritedName}_Banner.png"
            serieCoverPath = f"/static/img/mediaImages/{rewritedName}_Cover.png"
            description = res.overview
            note = res.vote_average
            date = res.first_air_date
            serieId = res.id
            details = show.details(serieId)
            cast = details.credits.cast
            cast = cast[:5]
            runTime = details.episode_run_time
            duration = ""
            for i in range(len(runTime)):
                if i != len(runTime)-1:
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
                    if bandeAnnonceType == "Trailer":
                        try:
                            bandeAnnonceUrl = websitesTrailers[bandeAnnonceHost] + bandeAnnonceKey
                            break
                        except KeyError as e:
                            bandeAnnonceUrl = "Unknown"
                            print(e)
            genreList = []
            for genre in serieGenre:
                genreList.append(genre.name)
            seasons = []
            serieData = {}
            for season in seasonsInfo:
                releaseDate = season.air_date
                episodesNumber = season.episode_count
                seasonNumber = season.season_number
                seasonId = season.id
                seasonName = season.name
                seasonDescription = season.overview
                seasonCoverPath = f"https://image.tmdb.org/t/p/original{season.poster_path}"

                allSeasonsUglyDict = allSeries[serie]["seasons"].keys()
                try:
                    allSeasons = [int(season) for season in allSeasonsUglyDict]
                except ValueError as e:
                    break
                seasonData = {}
                if seasonNumber in allSeasons:
                    for episode in allSeries[serie]["seasons"][str(seasonNumber)]:
                        slugs = allSeries[serie]["seasons"][str(seasonNumber)]
                        slug = slugs[episode]
                        slugReal = slug.replace(allSeriesPath, "")
                        slug = slug.replace(allSeriesPath, "http://localhost:8800")
                        episodeNumber = episode
                        episodePath = allSeries[serie]["seasons"][str(seasonNumber)][episodeNumber]
                        episodeName = episodePath.split("/")[-1]
                        episodeName, extension = os.path.splitext(episodeName)
                        episodeIndex = int(episodeName[1:])
                        showEpisode = Episode()
                        try:
                            episodeInfo = showEpisode.details(serieId, seasonNumber, episodeIndex)
                            coverEpisode = f"https://image.tmdb.org/t/p/original{episodeInfo.still_path}"
                            rewritedName = originalSerieTitle.replace(" ", "_")
                            if not os.path.exists(f"{currentCWD}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.png"):
                                with open(f"{currentCWD}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.png", 'wb') as f:
                                    f.write(requests.get(coverEpisode).content)
                            coverEpisode = f"/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.png"

                            thisEpisodeData = {"episodeName": episodeInfo.name, "episodeNumber": str(episodeInfo.episode_number), "episodeDescription": episodeInfo.overview, "episodeCoverPath": coverEpisode, "releaseDate": episodeInfo.air_date, "episodeSlug": slug, "slug": slugReal}
                            seasonData[episodeIndex] = thisEpisodeData
                        except TMDbException as e:
                            print(e)
                    seasonCoverPath = seasonCoverPath
                    if not os.path.exists(f"{currentCWD}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.png"):
                        with open(f"{currentCWD}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.png", 'wb') as f:
                            f.write(requests.get(seasonCoverPath).content)
                    seasonCoverPath = f"/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.png"
                    season = {"release": releaseDate, "episodesNumber": episodesNumber, "seasonNumber": seasonNumber, "seasonId": seasonId, "seasonName": seasonName, "seasonDescription": seasonDescription, "seasonCoverPath": seasonCoverPath, "episodes": seasonData}
                    seasons.append(season)
            try:
                episodeSlug = seasons[0]["episodes"][1]["episodeSlug"]
                episodeNumber = seasons[0]["episodes"][1]["episodeNumber"]
            except:
                episodeSlug = ""
                episodeNumber = "error"
            cast = cast[:5]
            for actor in cast:
                actorName = actor.name.replace(" ", "_").replace("/", "")
                actorImage = f"https://image.tmdb.org/t/p/original{actor.profile_path}"
                if not os.path.exists(f"{currentCWD}/static/img/mediaImages/Actor_{actorName}.png"):
                    with open(f"{currentCWD}/static/img/mediaImages/Actor_{actorName}.png", 'wb') as f:
                        f.write(requests.get(actorImage).content)
                actorImage = f"/static/img/mediaImages/Actor_{actorName}.png"
                actor.profile_path = actorImage
            serieData = {"name": name, "originalName": originalSerieTitle, "duration": duration, "genre": genreList,"serieId": serieId, "serieCoverPath": serieCoverPath, "banniere": banniere, "description": description, "note": note, "date": date, "cast": cast, "bandeAnnonce" : bandeAnnonceUrl, "firstEpisode": episodeSlug, "seasons": seasons}
            searchedSeries.append(serieData)
            allSeriesDict[name] = serieData

            with open(f"{currentCWD}/scannedFiles.json", 'r', encoding="utf8") as f:
                jsonFile = json.load(f)
                jsonFile["series"][name] = serieData
            with open(f"{currentCWD}/scannedFiles.json", "w", encoding="utf8") as f:
                json.dump(jsonFile, f, ensure_ascii=False, default=dict)
        else:
            with open(f"{currentCWD}/scannedFiles.json", 'r', encoding="utf8") as f:
                jsonFileToRead = json.load(f)
            data = jsonFileToRead["series"]
            data = data[name]
            serieData = data
            searchedSeries.append(serieData)
            allSeriesDict[name] = serieData

    allSeriesJson = jsonFileToRead["series"]
    for serie in allSeriesJson:
        name = serie
        slug = allSeriesJson[serie]["name"]
        series = os.listdir(allSeriesPath)
        if slug not in series:
            with open(f"{currentCWD}/scannedFiles.json", 'r', encoding="utf8") as f:
                jsonFile = json.load(f)
                del jsonFile["series"][name]
            with open(f"{currentCWD}/scannedFiles.json", "w", encoding="utf8") as f:
                json.dump(jsonFile, f, ensure_ascii=False)
    print()

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

@app.route("/serievideo/<serie>/<season>/<episode>.m3u8", methods=["GET"])
def createSerieM3U8(serie, season, episode):
    seriesPath = config.get("ChocolateSettings", "seriesPath")
    videoPath = os.path.join(seriesPath, serie, "Season "+season, "Episode "+episode+movieExtension)
    duration = length_video(videoPath)
    file = """
    #EXTM3U
    #EXT-X-VERSION:4
    #EXT-X-TARGETDURATION:5
    """

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""
        #EXTINF:5.0,
        /chunk/{serie}/{season}/{episode}-{(i // CHUNK_LENGTH) + 1}.ts
        """

    file += """
    #EXT-X-ENDLIST"
    """

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Content-Disposition", "attachment", filename=f"{episode}.m3u8")

    return response

@app.route("/video/<video_name>.m3u8", methods=["GET"])
def create_m3u8(video_name):
    moviesPath = config.get("ChocolateSettings", "MoviesPath")
    video_path = f"{moviesPath}\{video_name}{movieExtension}"
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
    global movieExtension
    seconds = (idx - 1) * CHUNK_LENGTH
    moviesPath = config.get("ChocolateSettings", "MoviesPath")
    video_path = f"{moviesPath}\{video_name}{movieExtension}"

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
            preset = "3"
            bitrate = "-b:v"
            bitrateValue = "5M"
            crf = "-crf"
            crfValue = "22"
            vsync = "-fps_mode"
            vsyncValue = "auto"
        else:
            videoCodec = "libx264"
            preset = "ultrafast"
    else:
        videoCodec = "libx264"
        preset = "ultrafast"
    print(serverGPU)
    logLevelValue = "error"
    movieVideoStats = get_video_properties(video_path)
    movieAudioStats = get_audio_properties(video_path)
    if movieAudioStats['codec_name'] == "aac" and movieVideoStats['codec_name'] == "h264":
        command = ["ffmpeg", "-loglevel", logLevelValue, "-hide_banner", "-ss", time_start, "-to", time_end, "-i", video_path,
                    "-output_ts_offset", time_start, "-c:v", "copy", "-c:a", "copy",  "-ac", "2", "-preset", "ultrafast", "-f", "mpegts", "pipe:1"]
    elif movieAudioStats['codec_name'] == "aac" and movieVideoStats['codec_name'] != "h264":
        print(f"AudioCodec: {movieAudioStats['codec_name']}")
        print(f"VideoCodec: {movieVideoStats['codec_name']}")

        if PIX:
            command = ["ffmpeg", "-loglevel", logLevelValue, "-hide_banner", "-ss", time_start, "-to", time_end, "-i", video_path,
                "-output_ts_offset", time_start, "-c:v", videoCodec, "-c:a", "copy", PIX, PIXcodec, "-ac", "2", "-preset", preset, bitrate, bitrateValue, crf, crfValue, vsync, vsyncValue, "-f", "mpegts", "pipe:1"]
        else:
            command = ["ffmpeg", "-loglevel", logLevelValue, "-hide_banner", "-ss", time_start, "-to", time_end, "-i", video_path,
               "-output_ts_offset", time_start, "-c:v", videoCodec, "-c:a", "copy",  "-ac", "2", "-preset", preset, "-f", "mpegts", "pipe:1"]

    elif movieAudioStats['codec_name'] != "aac" and movieVideoStats['codec_name'] == "h264":
        print(f"AudioCodec: {movieAudioStats['codec_name']}")
        print(f"VideoCodec: {movieVideoStats['codec_name']}")
        command = ["ffmpeg", "-loglevel", logLevelValue, "-hide_banner", "-ss", time_start, "-to", time_end, "-i", video_path,
               "-output_ts_offset", time_start, "-c:v", "copy", "-c:a", "aac",  "-ac", "2", "-preset", "ultrafast", "-f", "mpegts", "pipe:1"]
    else:
        print(f"AudioCodec: {movieAudioStats['codec_name']}")
        print(f"VideoCodec: {movieVideoStats['codec_name']}")
        if PIX:
            command = ["ffmpeg", "-loglevel", logLevelValue, "-hide_banner", "-ss", time_start, "-to", time_end, "-i", video_path,
               "-output_ts_offset", time_start, "-c:v", videoCodec, "-c:a", "aac", PIX, PIXcodec, "-ac", "2", "-preset", preset, bitrate, bitrateValue, crf, crfValue, vsync, vsyncValue, "-f", "mpegts", "pipe:1"]
        else:
            command = ["ffmpeg", "-loglevel", logLevelValue, "-hide_banner", "-ss", time_start, "-to", time_end, "-i", video_path,
               "-output_ts_offset", time_start, "-c:v", videoCodec, "-c:a", "aac", "-ac", "2", "-preset", preset, "-f", "mpegts", "pipe:1"]

    print((" ").join(command))

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)
    
    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Content-Disposition", "attachment", filename=f"{video_name}-{idx}.ts")

    return response

@app.route("/chunkCaption/<language>/<index>/<video_name>.vtt", methods=["GET"])
def chunkCaption(video_name, language, index):
    global movieExtension
    moviesPath = config.get("ChocolateSettings", "MoviesPath")
    video_path = f"{moviesPath}\{video_name}{movieExtension}"
    extractCaptionsCommand = ["ffmpeg", "-loglevel", "error", "-hide_banner", "-loglevel", "error", "-i", video_path, "-ac", "2", "-map", f"0:{index}", "-f", "webvtt", "pipe:1"]

    print(" ".join(extractCaptionsCommand))

    extractCaptions = subprocess.run(extractCaptionsCommand, stdout=subprocess.PIPE)

    extractCaptionsResponse = make_response(extractCaptions.stdout)
    extractCaptionsResponse.headers.set("Content-Type", "text/VTT")
    extractCaptionsResponse.headers.set("Content-Disposition", "attachment", filename=f"{video_name}-{index}.vtt")

    return extractCaptionsResponse

@app.route("/chunkAudio/<language>/<index>/<video_name>.mp3", methods=["GET"])
def chunkAudio(video_name, language, index):
    global movieExtension
    moviesPath = config.get("ChocolateSettings", "MoviesPath")
    video_path = f"{moviesPath}\{video_name}{movieExtension}"
    extractAudioCommand = ["ffmpeg", "-loglevel", "error", "-hide_banner", "-loglevel", "error", "-i", video_path, "-ac", "2", "-map", f"a:{index}", "-f", "mp3", "pipe:1"]

    print(" ".join(extractAudioCommand))

    extractAudio = subprocess.run(extractAudioCommand, stdout=subprocess.PIPE)

    extractAudioResponse = make_response(extractAudio.stdout)
    extractAudioResponse.headers.set("Content-Type", "audio/mpeg")
    extractAudioResponse.headers.set("Content-Disposition", "attachment", filename=f"{video_name}-{index}.mp3")

    return extractAudioResponse

@app.route("/settings")
def settings():
    global allMoviesNotSorted
    condition = len(allMoviesNotSorted) > 0
    return render_template("settings.html", notSorted=allMoviesNotSorted, conditionIfOne=condition)

@app.route("/saveSettings/", methods=['POST'])
def saveSettings():
    MoviesPath = request.form['moviesPath']
    SeriesPath = request.form['seriesPath']
    language = request.form['language']
    port = request.form['port']
    if MoviesPath != "":
        config.set("ChocolateSettings", "moviespath", MoviesPath)
    if SeriesPath != "":
        config.set("ChocolateSettings", "seriespath", SeriesPath)
    if language != "":
        config.set("ChocolateSettings", "language", language)
    if port != "":
        config.set("ChocolateSettings", "port", port)
    with open(f'{currentCWD}/config.ini', 'w') as conf:
        config.write(conf)
    return redirect(url_for('settings'))

#create a route to send all the movies to the page in a json
@app.route("/getAllMovies")
def getAllMovies():
    global simpleDataFilms
    simpleDataFilms.sort(key=lambda x: x["title"].lower())
    return json.dumps(simpleDataFilms, ensure_ascii=False)

@app.route("/getAllSeries")
def getAllSeries():
    global allSeriesDict
    allSeriesDictHere = dict(sorted(allSeriesDict.items()))

    return json.dumps(allSeriesDictHere, ensure_ascii=False, default=str, indent=4)

@app.route("/getRandomMovie")
def getRandomMovie():
    global simpleDataFilms
    randomMovie = random.choice(simpleDataFilms)
    return json.dumps(randomMovie, ensure_ascii=False)

@app.route("/getRandomSerie")
def getRandomSeries():
    global allSeriesDict
    randomSerie = random.choice(list(allSeriesDict.items()))
    return json.dumps(randomSerie, ensure_ascii=False, default=str)

def getSimilarMovies(movieId):
    global simpleDataFilms
    similarMoviesPossessed = []
    movie = Movie()
    similarMovies = movie.recommendations(movieId)
    for movieInfo in similarMovies:
        movieName = movieInfo.title
        for movie in simpleDataFilms:
            if movieName == movie["title"]:
                similarMoviesPossessed.append(movie)
                break
    return similarMoviesPossessed

def getSimilarSeries(seriesId):
    global allSeriesDict
    similarSeriesPossessed = []
    show = TV()
    similarSeries = show.recommendations(seriesId)
    for serieInfo in similarSeries:
        serieName = serieInfo.name
        for serie in allSeriesDict:
            try:
                if serieName == allSeriesDict[serie]["name"]:
                    similarSeriesPossessed.append(serie)
                    break
            except KeyError as e:
                print(e)
                pass
    return similarSeriesPossessed

@app.route("/getMovieData/<title>", methods=['GET', 'POST'])
def getMovieData(title):
    global allMoviesDict
    if title in allMoviesDict.keys():
        data = allMoviesDict[title]
        MovieId = data["id"]
        data["similarMovies"] = getSimilarMovies(MovieId)
        return json.dumps(data, ensure_ascii=False)
    else:
        return "Not Found"

@app.route("/getSerieData/<title>", methods=['GET', 'POST'])
def getSeriesData(title):
    global allSeriesDict
    if title in allSeriesDict.keys():
        data = allSeriesDict[title]
        SeriesId = data["serieId"]
        data["similarSeries"] = getSimilarSeries(SeriesId)
        return json.dumps(data, ensure_ascii=False, default=dict, indent=4)
    else:
        return "Not Found"

@app.route("/getFirstSevenMovies")
def getFirstEightMovies():
    global simpleDataFilms
    simpleDataFilms.sort(key=lambda x: x["title"].lower())
    return json.dumps(simpleDataFilms[:7], ensure_ascii=False)

@app.route("/getFirstSevenSeries")
def getFirstEightSeries():
    global allSeriesDict
    #get the first seven element of the dictionary
    allSeriesDict7 = dict(list(allSeriesDict.items())[:7])
    return json.dumps(list(allSeriesDict7.items()), ensure_ascii=False, default=str)

@app.route('/')
@app.route('/index')
@app.route('/home')
def home():
    moviesPath = config.get("ChocolateSettings", "MoviesPath")
    filmIsntEmpty = moviesPath != "Empty"
    return render_template('index.html', moviesExist=filmIsntEmpty)

@app.route("/movies")
def films():
    global allMoviesSorted
    searchedFilmsUp0 = len(searchedFilms) == 0
    errorMessage = "Verify that the path is correct"
    routeToUse = "/getFirstSevenMovies"

    return render_template('homeFilms.html', conditionIfOne=searchedFilmsUp0, errorMessage=errorMessage, routeToUse=routeToUse)

@app.route("/series")
def series():
    global allSeriesSorted
    searchedSeriesUp0 = len(searchedSeries) == 0
    errorMessage = "Verify that the path is correct"
    routeToUse = "/getFirstSevenSeries"

    return render_template('homeSeries.html', conditionIfOne=searchedSeriesUp0, errorMessage=errorMessage, routeToUse=routeToUse)

@app.route("/season/<name>/<id>")
def serie(name, id):
    global allSeriesDict
    if name in allSeriesDict.keys():
        data = allSeriesDict[name]
        return render_template('season.html', serie=data)
    else:
        return "Not Found"

@app.route("/getSeasonData/<serieName>/<seasonId>/")
def getSeasonData(serieName, seasonId):
    global allSeriesDict
    seasonId = int(seasonId[1:])-1
    if serieName in allSeriesDict.keys():
        data = allSeriesDict[serieName]
        print(len(data["seasons"]))
        season = data["seasons"][seasonId]
        return json.dumps(season, ensure_ascii=False, default=str)
    else:
        return "Not Found"

@app.route("/getEpisodeData/<serieName>/<seasonId>/<episodeId>/")
def getEpisodeData(serieName, seasonId, episodeId):
    global allSeriesDict
    seasonId = int(seasonId[1:])-1
    episodeId = int(episodeId[1:])-1
    if serieName in allSeriesDict.keys():
        data = allSeriesDict[serieName]
        season = data["seasons"][seasonId]
        episode = season["episodes"][episodeId]
        return json.dumps(episode, ensure_ascii=False, default=str)
    else:
        return "Not Found"

@app.route("/movieLibrary")
def library():
    global allMoviesSorted
    searchedFilmsUp0 = len(searchedFilms) == 0
    errorMessage = "Verify that the path is correct"
    routeToUse = "/getAllMovies"
    return render_template('allFilms.html', conditionIfOne=searchedFilmsUp0, errorMessage=errorMessage, routeToUse=routeToUse)

@app.route("/serieLibrary")
def seriesLibrary():
    global allSeriesSorted
    searchedSeriesUp0 = len(searchedSeries) == 0
    errorMessage = "Verify that the path is correct"
    routeToUse = "/getAllSeries"
    return render_template('allSeries.html', conditionIfOne=searchedSeriesUp0, errorMessage=errorMessage, routeToUse=routeToUse)

@app.route("/searchInMovies/<search>")
def searchInAllMovies(search):    
    global simpleDataFilms
    bestMatchs = {}
    movies = []
    points = {}

    for movie in simpleDataFilms:
        search = search.replace("%20", " ")
        distance = fuzz.ratio(search, movie["title"])
        points[movie["title"]] = distance

    bestMatchs = sorted(points.items(), key=lambda x: x[1], reverse=True)
    for movie in bestMatchs:
        thisMovie = movie[0]
        for films in simpleDataFilms:
            if films["title"] == thisMovie:
                movies.append(films)
                break
                
    return json.dumps(movies, ensure_ascii=False)

@app.route("/searchInSeries/<search>")
def searchInAllSeries(search):
    with open(f"{currentCWD}/scannedFiles.json", 'r', encoding="utf8") as f:
        jsonFileToRead = json.load(f)
        allSeriesJson = jsonFileToRead["series"]
    bestMatchs = {}
    series = []
    points = {}
    print(json.dumps(jsonFileToRead, indent=4))
    for serie in allSeriesJson:
        search = search.replace("%20", " ")
        distance = fuzz.ratio(search, serie["title"])
        points[serie["title"]] = distance

    bestMatchs = sorted(points.items(), key=lambda x: x[1], reverse=True)
    for serie in bestMatchs:
        thisSerie = serie[0]
        for series in allSeriesJson:
            if series["title"] == thisSerie:
                series.append(series)
                break
                
    return json.dumps(series, ensure_ascii=False)

@app.route("/search/movies/<search>")
def searchMovie(search):
    searchedFilmsUp0 = False
    errorMessage = "Verify your search terms"
    routeToUse = "/searchInMovies/" + search
    return render_template('allFilms.html', conditionIfOne=searchedFilmsUp0, errorMessage=errorMessage, routeToUse=routeToUse)

@app.route("/search/series/<search>")
def searchSerie(search):
    searchedFilmsUp0 = False
    errorMessage = "Verify your search terms"
    routeToUse = "/searchInSeries/" + search
    return render_template('allSeries.html', conditionIfOne=searchedFilmsUp0, errorMessage=errorMessage, routeToUse=routeToUse)



@app.route("/movie/<slug>")
def movie(slug):
    global filmEncode, movieExtension
    if not slug.endswith("ttf"):
        rewriteSlug, movieExtension = os.path.splitext(slug)
        link = f"/video/{rewriteSlug}.m3u8".replace(" ", "%20") 
    allCaptions = generateCaption(slug)
    return render_template("film.html", slug=slug, movieUrl=link, allCaptions=allCaptions)

@app.route("/series/<name>/<saison>/<slug>")
def seriesPlayer(name, saison, slug):
    global filmEncode, movieExtension
    if not slug.endswith("ttf"):
        rewriteSlug, movieExtension = os.path.splitext(slug)
        link = f"/video/{rewriteSlug}.m3u8".replace(" ", "%20") 
        allCaptions = generateCaption(slug)
        return render_template("film.html", slug=slug, movieUrl=link, allCaptions=allCaptions)

def generateCaption(slug):
    captionCommand = ["ffprobe", "-loglevel", "error", "-select_streams", "s", "-show_entries", "stream=index:stream_tags=language", "-of", "csv=p=0", slug]
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
        'eng': 'English',
        'fre': 'Français',
        'spa': 'Español',
        'por': 'Português',
        'ita': 'Italiano',
        'ger': 'Deutsch',
        'rus': 'Русский',
        'pol': 'Polski',
        'por': 'Português',
        'chi': '中文',
        'srp': 'Srpski',
        }

    captionResponse.pop()

    for line in captionResponse:
        line = line.rstrip()
        language = line.split(",")[1]
        index = line.split(",")[0]
        allCaptions.append({"index": index, "languageCode" : language, "language": languages[language], "url":f"/chunkCaption/{language}/{index}/{rewriteSlug}.vtt"})
    
    return allCaptions

@app.route("/generateAudio/<slug>")
def generateAudio(slug):
    audioCommand = ["ffprobe", "-loglevel", "error", "-select_streams", "a", "-show_entries", "stream=index:stream_tags=language", "-of", "csv=p=0", slug]
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
        'eng': 'English',
        'fre': 'Français',
        'spa': 'Español',
        'por': 'Português',
        'ita': 'Italiano',
        'ger': 'Deutsch',
        'rus': 'Русский',
        'pol': 'Polski',
        'por': 'Português',
        'chi': '中文',
        'srp': 'Srpski',
        }
    for line in audioResponse:
        line = line.rstrip()
        language = line.split(",")[1]
        index = line.split(",")[0]
        allAudio.append({"index": index, "languageCode" : language, "language": languages[language], "url":f"/chunkAudio/{language}/{index}/{rewriteSlug}.mp3"})

    return allAudio


@app.route("/actor/<actorName>")
def actor(actorName):
    routeToUse = "/getActorData/" + actorName
    return render_template("actor.html", routeToUse=routeToUse)

@app.route("/getActorData/<actorName>", methods=['GET', 'POST'])
def getActorData(actorName):
    global searchedFilms, simpleDataFilms
    movies = []
    person = Person()
    actorDatas = person.search(actorName)
    for movie in searchedFilms:
        actors = movie["cast"]
        for actor in actors:
            if actor[0] == actorName:
                for movieData in simpleDataFilms:
                    if movie["title"] == movieData["title"]:
                        movies.append(movie)
                        break
    actorId = actorDatas[0].id
    p = person.details(actorId)
    name = p["name"]
    birthday = p["birthday"]
    birthplace = p["place_of_birth"]
    actorDescription = p["biography"]
    rewritedName = name.replace(" ", "_")
    actorData = {
        "actorName": name,
        "actorImage": f"/static/img/mediaImages/Actor_{rewritedName}.png",
        "actorDescription": actorDescription,
        "actorBirthday": birthday,
        "actorBirthplace": birthplace,
        "actorMovies": movies
    }
    return json.dumps(actorData, default=lambda o: o.__dict__, ensure_ascii=False)

if __name__ == '__main__':
    getSeries()
    getMovies()
    print('\033[?25h', end="")
    app.run(host="0.0.0.0", port=serverPort)