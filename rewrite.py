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
serie = "Kaamelott"
show = TV()
serieTitle = serie
originalSerieTitle = serieTitle

try:
    search = show.search(serieTitle)
except TMDbException:
    print(TMDbException)
    allSeriesNotSorted.append(serieTitle)
                    
if not search:
    allSeriesNotSorted.append(serieTitle)
        
bestMatch = search[0]
res = bestMatch
name = res.name
serieCoverPath = f"https://image.tmdb.org/t/p/original{res.poster_path}"
banniere = f"https://image.tmdb.org/t/p/original{res.backdrop_path}"
description = res.overview
note = res.vote_average
date = res.first_air_date
serieId = res.id
details = show.details(serieId)
seasonsInfo = details.seasons
episode = 0
for season in seasonsInfo:
    episodeStart = episode
    episodeEnd = season.episode_count
    episode+=episodeEnd
    print(f"Saison numéro {season.season_number} : {episodeStart+1} - {episode}")

print(seasonsInfo)