
import configparser, os, re, cv2, imagehash, time, colorama
from PIL import Image
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)
config = configparser.ConfigParser()
dir = os.path.dirname(__file__)
config.read(os.path.join(dir, "config.ini"))

colorama.init()

dirPath = os.path.dirname(__file__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{dirPath}/database.db"
app.config['MAX_CONTENT_LENGTH'] = 4096 * 4096
app.config['UPLOAD_FOLDER'] = f"{dirPath}/static/img/"
app.config['SECRET_KEY'] = "ChocolateDBPassword"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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

with app.app_context():
  db.init_app(app)

def listAllSeasons():
    libraries = Libraries.query.all()
    for library in libraries:
        libType = library.libType
        if libType == "series":
            seriesPath = library.libFolder
            series = Series.query.filter_by(libraryName=library.libName).all()
            seriesIntro = {}
            for serie in series:
                serie = serie.__dict__
                del serie['_sa_instance_state']
                seriePath2 = f"{seriesPath}/{serie['originalName']}"
                allSeasonData = {}
                for seasons in os.listdir(seriePath2):
                    seasonPath = f"{seriePath2}/{seasons}"
                    findPath = seasonPath.replace(seriesPath, "")
                    print(f"Detecing intro for {serie['originalName']} {seasons} ")
                    allEpisodesData = detectIntro(seasonPath, library.libName, findPath, serie['originalName'])
                    allSeasonData[seasons] = allEpisodesData


def detectIntro(mainPath, libName, findPath, seasonName):
    episodesListe1 = listAllVideoFiles(mainPath)
    episodesListe1.sort(key=lambda f: int(re.sub("\D", "", f)))
    episodesData = {}
    librarie = Libraries.query.filter_by(libName=libName).first()
    seriesPath = librarie.libFolder
    for episode1 in episodesListe1:
        
        episodeSlug = f"{mainPath}/{episode1}".replace("\\", "/")
        episodeFindPath = f"{findPath}/{episode1}".replace("\\", "/")
        episodeSlug = episodeSlug.replace(seriesPath, "")
        episodeData = Episodes.query.filter_by(slug=episodeFindPath).first()
        a = bool(episodeData.introStart == 0.0) # if introStart is 0.0, then it"s not set
        b = bool(episodeData.introEnd == 0.0) # if introEnd is 0.0, then it"s not set
        c = bool(a and b) # if both are 0.0, then it"s not set
        #print(f"Pour l"épisode {episodeSlug}, a = {a}, b = {b}, c = {c}")
        if (a ^ b) or c:
            episodeOneData = {}
            episodeOneData['name'] = episode1
            episodeOneData['start'] = None
            episodeOneData['end'] = None
            episode1Index = episodesListe1.index(episode1)
            if episode1Index < len(episodesListe1) - 1:
                episode2 = episodesListe1[episode1Index + 1]
            else:
                episode2 = episodesListe1[episode1Index-1]

            videoFile1 = f"{mainPath}/{episode1}"
            videoFile2 = f"{mainPath}/{episode2}"
            cap1 = cv2.VideoCapture(videoFile1)
            cap2 = cv2.VideoCapture(videoFile2)
            
            #get the frameRate of the video
            frameRate1 = cap1.get(cv2.CAP_PROP_FPS)
            frameRate2 = cap2.get(cv2.CAP_PROP_FPS)

            frameCount1 = int(cap1.get(cv2.CAP_PROP_FRAME_COUNT))
            frameCount2 = int(cap2.get(cv2.CAP_PROP_FRAME_COUNT))

            maxFrame1 = round(frameRate1 * 60*5)
            maxFrame2 = round(frameRate2 * 60*5)


            #print(f"Serie: {mainPath}")
            #print(f"videoName: {episode1} - maxFrame1: {maxFrame1} - frameCount1: {frameCount1} - frameRate1: {frameRate1}\nvideoName: {episode2} - maxFrame2: {maxFrame2} - frameCount2: {frameCount2} - frameRate2: {frameRate2}")
            searchForIntroStart = True
            secondesEp1 = []
            ep1Start = 0
            secondesEp2 = []
            ratio = (int(160/2), int(90/2))
            for frameEp1 in range(1, maxFrame1, round(frameRate1)):
                cap1.set(1, frameEp1)
                ret1, frame1 = cap1.read()
                frame1 = cv2.resize(frame1, ratio, interpolation = cv2.INTER_LINEAR)
                frame1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
                frame1 = str(imagehash.dhash(Image.fromarray(frame1)))
                secondesEp1.append(frame1)
                #print(f"frameEp1: {str(frameEp1).zfill(4)} - frame1: {frame1}")
            for frameEp2 in range(1,maxFrame2, round(frameRate2)):
                cap2.set(1, frameEp2)
                ret1, frame2 = cap2.read()
                frame2 = cv2.resize(frame2, ratio, interpolation = cv2.INTER_LINEAR)
                frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
                frame2 = str(imagehash.dhash(Image.fromarray(frame2)))
                secondesEp2.append(frame2)
                #print(f"frameEp2: {str(frameEp2).zfill(4)} - frame2: {frame2}")
            while searchForIntroStart:
                for frame1 in secondesEp1:
                    #print(f"Searching {frame1} in secondesEp2")
                    if frame1 in secondesEp2:
                        ep1StartIndex = secondesEp1.index(frame1)
                        ep1Start = ep1StartIndex
                        episodeOneData['start'] = ep1Start

                        ep2StartIndex = secondesEp2.index(frame1)
                        searchForIntroStart = False
                        break
            #print(f"J"ai trouvé le départ de l"intro à {ep1Start}s dans {episode1} et {ep2StartIndex}s dans {episode2}")
            secondesEp1 = secondesEp1[ep1StartIndex:]
            secondesEp2 = secondesEp2[ep2StartIndex:]
            #print(secondesEp1)
            
            for frame in secondesEp1:
                secondes = secondesEp1.index(frame)
                if frame in secondesEp2:
                    episodeOneData['end'] = secondes
                elif episodeOneData['end'] is not None and secondes<episodeOneData['end']+3:
                    episodeOneData['end'] = secondes
                else:
                    break


            episode = Episodes.query.filter_by(slug=episodeFindPath).first()
            season = Seasons.query.filter_by(seasonId=episodeData.seasonId).first()
            if episode:
                """
                episode.introStart = episodeOneData['start']
                episode.introEnd = episodeOneData['end']"""
                episodeStartInMM_SS = time.strftime("%M:%S", time.gmtime(episodeOneData['start']))
                episodeEndInMM_SS = time.strftime("%M:%S", time.gmtime(episodeOneData['end']))
                introDuration = episodeOneData['end'] - episodeOneData['start']
                introDurationInMM_SS = time.strftime("%M:%S", time.gmtime(introDuration))
                print(f"{colorama.Fore.RED}{seasonName}{colorama.Fore.RESET} - {colorama.Fore.BLUE}S{season.seasonNumber}{colorama.Fore.RESET} - {colorama.Fore.CYAN}E{episode.episodeNumber}{colorama.Fore.RESET} : [ {colorama.Fore.GREEN}Intro start: {episodeStartInMM_SS} ({episodeOneData['start']}s){colorama.Fore.RESET} - {colorama.Fore.YELLOW}Intro end: {episodeEndInMM_SS} ({episodeOneData['end']}s){colorama.Fore.RESET} ] - {colorama.Fore.LIGHTBLUE_EX}Duration: {introDurationInMM_SS} ({introDuration}s){colorama.Fore.RESET}")
                #db.session.commit()


def listAllVideoFiles(seasonPath):
    episodes = []
    for episode in os.listdir(seasonPath):
        if episode.endswith(".mp4") or episode.endswith(".mkv") or episode.endswith(".avi") or episode.endswith(".mov") or episode.endswith(".wmv"):
            episodes.append(episode)
    return episodes

import os, subprocess
from pydub import AudioSegment

# Fonction pour extraire le flux audio des vidéos
def extract_audio(video_file, audio_file):
    command = f'ffmpeg -i "{video_file}" {audio_file}'
    command = [
        "ffmpeg",
        "-i",
        video_file,
        audio_file
    ]
    subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    

# Fonction pour comparer et trouver les séquences audio similaires
def compare_audio(audio_file_1, audio_file_2, threshold):
    audio_1 = AudioSegment.from_file(audio_file_1, "wav")
    audio_2 = AudioSegment.from_file(audio_file_2, "wav")
    #remove the audio files
    os.remove(audio_file_1)
    os.remove(audio_file_2)
    audio_chunks_1 = audio_1[::1000]
    audio_chunks_2 = audio_2[::1000]
    similar_chunks = []
    for chunk in audio_chunks_1:
        for chunk2 in list(audio_chunks_2):
            if abs(chunk.dBFS - chunk2.dBFS) < threshold:
                similar_chunks.append((list(audio_chunks_2).index(chunk2), chunk.duration_seconds))
                break
    return similar_chunks

# Fonction principale
def main(video_file_1, video_file_2, threshold):
    audio_file_1 = os.path.splitext(video_file_1)[0] + ".wav"
    audio_file_2 = os.path.splitext(video_file_2)[0] + ".wav"
    extract_audio(video_file_1, audio_file_1)
    extract_audio(video_file_2, audio_file_2)
    similar_chunks = compare_audio(audio_file_1, audio_file_2, threshold)
    for i, duration in similar_chunks:
        print(f"Séquence similaire trouvée à partir de la {i}ème seconde avec une durée de {duration} secondes.")

# Exécuter la fonction principale
if __name__ == "__main__":
    with app.app_context():
        allSeriesLibrary = Libraries.query.filter_by(libType="series").all()
        for library in allSeriesLibrary:
            allSeries = Series.query.filter_by(libraryName=library.libName).all()
            for serie in allSeries:
                allSeasons = Seasons.query.filter_by(serie=serie.id).all()
                for season in allSeasons:
                    allEpisodes = Episodes.query.filter_by(seasonId=season.seasonId).all()
                    #order alphabetically
                    allEpisodes.sort(key=lambda f: f.slug)
                    
                    for episode in range(0, len(allEpisodes)-1):
                        episode1 = allEpisodes[episode]
                        episode2 = allEpisodes[episode+1]
                        basePath = f"{library.libFolder}".replace("\\", "/")
                        episode1Path = f"{basePath}{episode1.slug}"
                        episode2Path = f"{basePath}{episode2.slug}"
                        threshold = 3.0 # Modifiez le seuil dBFS ici
                        print(f"Calculating for {episode1.slug} and {episode2.slug}")
                        main(episode1Path, episode2Path, threshold)