import os, json, subprocess, requests
from bs4 import BeautifulSoup
from tmdbv3api import TMDb, Movie, TV, Episode
from tmdbv3api.exceptions import TMDbException
from Levenshtein import distance as lev

currentCWD = os.getcwd()
allSeriesPath = "G:/Films-Series-Emissions/Series"
tmdb = TMDb()
tmdb.api_key = 'cb862a91645ec50312cf636826e5ca1f'
tmdb.language = "fr-FR"
tmdb.debug = True

searchedSeries = []
simpleDataSeries = {}
allSeriesNotSorted = []
allSeriesDict = {}

def getSeries():
    allSeries = [ name for name in os.listdir(allSeriesPath) if os.path.isdir(os.path.join(allSeriesPath, name)) ]
    allSeasonsAppelations = ["S"]
    allEpisodesAppelations = ["E"]

    allSeriesDict = {}

    for series in allSeries:
        seasons = os.listdir(f"{allSeriesPath}\\{series}")
        serieSeasons = {}
        for season in seasons:
            path = f"{allSeriesPath}/{series}"
            if season.startswith(tuple(allSeasonsAppelations)) and season.endswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")):
                pass
            else:
                allSeasons = os.listdir(f"{path}")
                for allSeason in allSeasons:
                    actualName = f"{series}/{allSeason}"
                    os.rename(f"{path}/{allSeason}", f"{path}/S{allSeasons.index(allSeason)+1}")

            episodesPath = f"{path}/{season}"
            #get the season number
            try:
                seasonNumber = season.split(" ")[1]
            except Exception as e:
                seasonNumber = season[1:]
            episodes = os.listdir(episodesPath)
            seasonEpisodes = {}
            for episode in episodes:
                if os.path.isfile(f"{episodesPath}/{episode}"):
                    if episode.startswith(tuple(allEpisodesAppelations)) and episode.endswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")):
                        pass
                    else:
                        actualName = f"{episodesPath}/{episode}"
                        episodeName, extension =  os.path.splitext(episode)
                        oldIndex = episodes.index(episode)
                        try:
                            os.rename(f"{episodesPath}/{episode}", f"{episodesPath}/E{episodes.index(episode)+1}{extension}")
                        except FileExistsError:
                            pass
                        episode = f"E{oldIndex+1}{extension}"
                    #add episodes to a season list
                    seasonEpisodes[oldIndex+1] = f"{path}/{season}/{episode}"
            serieSeasons[seasonNumber] = seasonEpisodes

        serieData = {}
        serieData["seasons"] = serieSeasons
        allSeriesDict[series] = serieData


    allSeries = allSeriesDict
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
            continue
        show = TV()
        serieTitle = serie
        originalSerieTitle = serieTitle

        try:
            search = show.search(serieTitle)
        except TMDbException:
            print(TMDbException)
            allSeriesNotSorted.append(serieTitle)
            break
                    
        if not search:
            allSeriesNotSorted.append(serieTitle)
            break
        
        index = allSeriesName.index(serieTitle)
        print(f"{index+1}/{len(allSeriesName)}")
                
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
        serieCoverPath = f"https://image.tmdb.org/t/p/original{res.poster_path}"
        banniere = f"https://image.tmdb.org/t/p/original{res.backdrop_path}"
        description = res.overview
        note = res.vote_average
        date = res.first_air_date
        serieId = res.id
        details = show.details(serieId)
        cast = res.credits.cast
        seasonsInfo = details.seasons
        duration = f"{details.episode_run_time[0]}:{details.episode_run_time[1]}:{details.episode_run_time[2]}"
        seasons = []
        for season in seasonsInfo:
            releaseDate = season.air_date
            episodesNumber = season.episode_count
            seasonNumber = season.season_number
            seasonId = season.id
            seasonName = season.name
            seasonDescription = season.overview
            seasonCoverPath = f"https://image.tmdb.org/t/p/original{season.poster_path}"

            allSeasonsUglyDict = allSeries[serie]["seasons"].keys()
            allSeasons = [int(season) for season in allSeasonsUglyDict]
            seasonData = {}
            if seasonNumber in allSeasons:
                for episode in allSeries[serie]["seasons"][str(seasonNumber)]:
                    slugs = allSeries[serie]["seasons"][str(seasonNumber)]
                    slug = slugs[episode]
                    slug = slug.replace(allSeriesPath, "http://localhost:8800")
                    episodeNumber = episode
                    episodePath = allSeries[serie]["seasons"][str(seasonNumber)][episodeNumber]
                    episodeName = episodePath.split("/")[-1]
                    episodeName, extension = os.path.splitext(episodeName)
                    episodeIndex = int(episodeName[1:])
                    showEpisode = Episode()
                    try:
                        episodeInfo = showEpisode.details(serieId, seasonNumber, episodeIndex)
                        thisEpisodeData = {"episodeName": episodeInfo.name, "episodeNumber": str(episodeInfo.episode_number), "episodeDescription": episodeInfo.overview, "episodeCoverPath": f"https://image.tmdb.org/t/p/original{episodeInfo.still_path}","crew": episodeInfo.crew, "releaseDate": episodeInfo.air_date, "episodeSlug": slug}
                        #print all the type of the values of the episode
                        seasonData[episodeIndex] = thisEpisodeData
                    except TMDbException:
                        continue
                    print(f"{serie} S{seasonNumber}E{episodeNumber} / S{len(allSeasons)}E{episodesNumber}")
                season = {"release": releaseDate, "episodesNumber": episodesNumber, "seasonNumber": seasonNumber, "seasonId": seasonId, "seasonName": seasonName, "seasonDescription": seasonDescription, "seasonCoverPath": seasonCoverPath, "episodes": seasonData}
                seasons.append(season)
        serieData = {"name": name, "originalName": originalSerieTitle,"serieId": serieId, "serieCoverPath": serieCoverPath, "banniere": banniere, "description": description, "note": note, "date": date, "seasons": seasons, "cast": cast}
        searchedSeries.append(serieData)
        allSeriesDict[name] = serieData
    print(json.dumps(searchedSeries, indent=4, default=str))

getSeries()