import configparser, os, re, cv2, imagehash
from PIL import Image
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)
config = configparser.ConfigParser()
dir = os.path.dirname(__file__)
config.read(os.path.join(dir, 'config.ini'))

dirPath = os.path.dirname(__file__)
app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///{dirPath}/database.db'
app.config['MAX_CONTENT_LENGTH'] = 4096 * 4096
app.config['UPLOAD_FOLDER'] = f"{dirPath}/static/img/"
app.config["SECRET_KEY"] = "ChocolateDBPassword"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

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

    def __init__(self, id, name, originalName, genre, duration, description, cast, bandeAnnonceUrl, serieCoverPath, banniere, note, date, serieModifiedTime):
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
    
    def __repr__(self) -> str:
        return f"<Series {self.name}>"

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
    series = Series.query.all()
    seriesPath = config["ChocolateSettings"]["seriespath"]
    seriesIntro = {}
    for serie in series:
        serie = serie.__dict__
        del serie["_sa_instance_state"]
        seriePath = f"{seriesPath}/{serie['originalName']}"
        allSeasonData = {}
        for seasons in os.listdir(seriePath):
            seasonPath = f"{seriePath}/{seasons}"
            allEpisodesData = detectIntro(seasonPath)
            allSeasonData[seasons] = allEpisodesData
        seriesIntro[serie["originalName"]] = allSeasonData

def detectIntro(mainPath):
    episodesListe1 = listAllVideoFiles(mainPath)
    episodesListe1.sort(key=lambda f: int(re.sub('\D', '', f)))
    episodesData = {}
    for episode1 in episodesListe1:
        
        episodeSlug = f"{mainPath}/{episode1}".replace("\\", "/")
        seriesPath = config["ChocolateSettings"]["seriespath"].replace("\\", "/")
        episodeSlug = episodeSlug.replace(seriesPath, "")
        episodeData = Episodes.query.filter_by(slug=episodeSlug).first()
        a = bool(episodeData.introStart == 0.0) # if introStart is 0.0, then it's not set
        b = bool(episodeData.introEnd == 0.0) # if introEnd is 0.0, then it's not set
        c = bool(a and b) # if both are 0.0, then it's not set
        #print(f"Pour l'épisode {episodeSlug}, a = {a}, b = {b}, c = {c}")
        if (a ^ b) or c:
            print(f"Detecting intro for {episode1}, {episodeSlug}")
            episodeOneData = {}
            episodeOneData["name"] = episode1
            episodeOneData["start"] = None
            episodeOneData["end"] = None
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

            #keep only the first 180 seconds of the video


            #print(f"Serie: {mainPath}")
            #print(f"videoName: {episode1} - maxFrame1: {maxFrame1} - frameCount1: {frameCount1} - frameRate1: {frameRate1}\nvideoName: {episode2} - maxFrame2: {maxFrame2} - frameCount2: {frameCount2} - frameRate2: {frameRate2}")
            searchForIntroStart = True
            secondesEp1 = []
            ep1Start = 0
            secondesEp2 = []
            for frameEp1 in range(1, maxFrame1, round(frameRate1)):
                cap1.set(1, frameEp1)
                ret1, frame1 = cap1.read()
                ratio1 = (160, 90)
                frame1 = cv2.resize(frame1, ratio1, interpolation = cv2.INTER_LINEAR)
                frameHash1 = str(imagehash.dhash(Image.fromarray(frame1)))
                secondesEp1.append(frameHash1)
                #print(f"frameEp1: {str(frameEp1).zfill(4)} - frame1: {frameHash1}")
            for frameEp2 in range(1,maxFrame2, round(frameRate2)):
                cap2.set(1, frameEp2)
                ret1, frame2 = cap2.read()
                ratio2 = (160, 90)
                frame2 = cv2.resize(frame2, ratio2, interpolation = cv2.INTER_LINEAR)
                frameHash2 = str(imagehash.dhash(Image.fromarray(frame2)))
                secondesEp2.append(frameHash2)
                #print(f"frameEp2: {str(frameEp2).zfill(4)} - frame2: {frameHash2}")
            while searchForIntroStart:
                for frame1 in secondesEp1:
                    #print(f"Searching {frame1} in secondesEp2")
                    if frame1 in secondesEp2:
                        ep1StartIndex = secondesEp1.index(frame1)
                        ep1Start = ep1StartIndex
                        episodeOneData["start"] = ep1Start

                        ep2StartIndex = secondesEp2.index(frame1)
                        searchForIntroStart = False
                        break
            #print(f"J'ai trouvé le départ de l'intro à {ep1Start}s dans {episode1} et {ep2StartIndex}s dans {episode2}")
            secondesEp1 = secondesEp1[ep1StartIndex:]
            secondesEp2 = secondesEp2[ep2StartIndex:]
            #print(secondesEp1)
            for frame in secondesEp1:
                secondes = secondesEp1.index(frame)
                if frame in secondesEp2:
                    episodeOneData["end"] = secondes
                elif secondes<episodeOneData["end"]+10:
                    episodeOneData["end"] = secondes
                else:
                    break
            episode = Episodes.query.filter_by(slug=episodeSlug).first()
            if episode:
                episode.introStart = episodeOneData["start"]
                episode.introEnd = episodeOneData["end"]
                db.session.commit()


def listAllVideoFiles(seasonPath):
    episodes = []
    for episode in os.listdir(seasonPath):
        if episode.endswith(".mp4") or episode.endswith(".mkv") or episode.endswith(".avi") or episode.endswith(".mov") or episode.endswith(".wmv"):
            episodes.append(episode)
    return episodes

if __name__ == "__main__":
    with app.app_context():
        listAllSeasons()