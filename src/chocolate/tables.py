from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from time import time

from . import DB

class Users(DB.Model, UserMixin):
    id = DB.Column(DB.Integer, primary_key=True, autoincrement=True)
    name = DB.Column(DB.String(255), unique=True)
    password = DB.Column(DB.String(255))
    profil_picture = DB.Column(DB.String(255))
    account_type = DB.Column(DB.String(255))

    def __init__(self, name, password, profil_picture, account_type):
        self.name = name
        if password != None and password != "":
            self.password = generate_password_hash(password)
        else:
            self.password = None
        self.profil_picture = profil_picture
        self.account_type = account_type

    def __repr__(self) -> str:
        return f'<Name {self.name}>'

    def verify_password(self, pwd):
        if self.password == None:
            return True
        return check_password_hash(self.password, pwd)

class Movies(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    title = DB.Column(DB.String(255), primary_key=True)
    real_title = DB.Column(DB.String(255), primary_key=True)
    cover = DB.Column(DB.String(255))
    banner = DB.Column(DB.String(255))
    slug = DB.Column(DB.String(255))
    description = DB.Column(DB.String(2550))
    note = DB.Column(DB.String(255))
    date = DB.Column(DB.String(255))
    genre = DB.Column(DB.String(255))
    duration = DB.Column(DB.String(255))
    cast = DB.Column(DB.String(255))
    bande_annonce_url = DB.Column(DB.String(255))
    adult = DB.Column(DB.String(255))
    library_name = DB.Column(DB.String(255))
    alternatives_names = DB.Column(DB.Text)

    def __init__(self, id, title, real_title, cover, banner, slug, description, note, date, genre, duration, cast, bande_annonce_url, adult, library_name, alternatives_names):
        self.id = id
        self.title = title
        self.real_title = real_title
        self.cover = cover
        self.banner = banner
        self.slug = slug
        self.description = description
        self.note = note
        self.date = date
        self.genre = genre
        self.duration = duration
        self.cast = cast
        self.bande_annonce_url = bande_annonce_url
        self.adult = adult
        self.library_name = library_name
        self.alternatives_names = alternatives_names

    def __repr__(self) -> str:
        return f"<Movies {self.title}>"


class Series(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.String(255), primary_key=True)
    original_name = DB.Column(DB.String(255), primary_key=True)
    genre = DB.Column(DB.String(255))
    duration = DB.Column(DB.String(255))
    description = DB.Column(DB.String(2550))
    cast = DB.Column(DB.String(255))
    bande_annonce_url = DB.Column(DB.String(255))
    serie_cover_path = DB.Column(DB.String(255))
    banniere = DB.Column(DB.String(255))
    note = DB.Column(DB.String(255))
    date = DB.Column(DB.String(255))
    serie_modified_time = DB.Column(DB.Float)
    library_name = DB.Column(DB.String(255))
    adult = DB.Column(DB.String(255))

    def __init__(self, id, name, original_name, genre, duration, description, cast, bande_annonce_url, serie_cover_path, banniere, note, date, serie_modified_time, adult, library_name):
        self.id = id
        self.name = name
        self.original_name = original_name
        self.genre = genre
        self.duration = duration
        self.description = description
        self.cast = cast
        self.bande_annonce_url = bande_annonce_url
        self.serie_cover_path = serie_cover_path
        self.banniere = banniere
        self.note = note
        self.date = date
        self.serie_modified_time = serie_modified_time
        self.library_name = library_name
        self.adult = adult

    def __repr__(self) -> str:
        return f"<Series {self.name}>"


class Seasons(DB.Model):

    serie = DB.Column(DB.Integer, nullable=False)
    season_id = DB.Column(DB.Integer, primary_key=True)
    season_number = DB.Column(DB.Integer, primary_key=True)
    release = DB.Column(DB.String(255))
    episodes_number = DB.Column(DB.String(255))
    season_name = DB.Column(DB.String(255))
    season_description = DB.Column(DB.Text)
    season_cover_path = DB.Column(DB.String(255))
    modified_date = DB.Column(DB.Float)
    number_of_episode_in_folder = DB.Column(DB.Integer)

    def __init__(self, serie, release, episodes_number, season_number, season_id, season_name, season_description, season_cover_path, modified_date, number_of_episode_in_folder):
        self.serie = serie
        self.release = release
        self.episodes_number = episodes_number
        self.season_number = season_number
        self.season_id = season_id
        self.season_name = season_name
        self.season_description = season_description
        self.season_cover_path = season_cover_path
        self.modified_date = modified_date
        self.number_of_episode_in_folder = number_of_episode_in_folder

    def __repr__(self) -> str:
        return f"<Seasons {self.serie} {self.season_number}>"


class Episodes(DB.Model):
    season_id = DB.Column(DB.Integer, nullable=False)
    episode_id = DB.Column(DB.Integer, primary_key=True)
    episode_name = DB.Column(DB.String(255), primary_key=True)
    episode_number = DB.Column(DB.Integer, primary_key=True)
    episode_description = DB.Column(DB.Text)
    episode_cover_path = DB.Column(DB.String(255))
    release_date = DB.Column(DB.String(255))
    slug = DB.Column(DB.String(255))
    intro_start = DB.Column(DB.Float)
    intro_end = DB.Column(DB.Float)

    def __init__(self, season_id, episode_id, episode_name, episode_number, episode_description, episode_cover_path, release_date, slug, intro_start, intro_end):
        self.season_id = season_id
        self.episode_id = episode_id
        self.episode_name = episode_name
        self.episode_number = episode_number
        self.episode_description = episode_description
        self.episode_cover_path = episode_cover_path
        self.release_date = release_date
        self.slug = slug
        self.intro_start = intro_start
        self.intro_end = intro_end

    def __repr__(self) -> str:
        return f"<Episodes {self.season_id} {self.episodeNumber}>"


class Games(DB.Model):
    console = DB.Column(DB.String(255), nullable=False)
    id = DB.Column(DB.Integer, primary_key=True)
    title = DB.Column(DB.String(255), primary_key=True)
    real_title = DB.Column(DB.String(255), primary_key=True)
    cover = DB.Column(DB.String(255))
    description = DB.Column(DB.String(2550))
    note = DB.Column(DB.String(255))
    date = DB.Column(DB.String(255))
    genre = DB.Column(DB.String(255))
    slug = DB.Column(DB.String(255))
    library_name = DB.Column(DB.String(255))

    def __init__(self, console, id, title, real_title, cover, description, note, date, genre, slug, library_name):
        self.console = console
        self.id = id
        self.title = title
        self.real_title = real_title
        self.cover = cover
        self.description = description
        self.note = note
        self.date = date
        self.genre = genre
        self.slug = slug
        self.library_name = library_name

    def __repr__(self) -> str:
        return f"<Games {self.title}>"


class OthersVideos(DB.Model):
    video_hash = DB.Column(DB.String(255), primary_key=True)
    title = DB.Column(DB.String(255), primary_key=True)
    slug = DB.Column(DB.String(255))
    banner = DB.Column(DB.String(255))
    duration = DB.Column(DB.String(255))
    library_name = DB.Column(DB.String(255))

    def __init__(self, video_hash, title, slug, banner, duration, library_name):
        self.video_hash = video_hash
        self.title = title
        self.slug = slug
        self.banner = banner
        self.duration = duration
        self.library_name = library_name

    def __repr__(self) -> str:
        return f"<OthersVideos {self.title}>"


class Books(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True, autoincrement=True)
    title = DB.Column(DB.String(255))
    slug = DB.Column(DB.String(255))
    book_type = DB.Column(DB.String(255))
    cover = DB.Column(DB.String(255))
    library_name = DB.Column(DB.String(255))

    def __repr__(self) -> str:
        return f"<Books {self.title}>"


class Artist(DB.Model):
    """
    Artist model

    ...

    Attributes
    ----------
    id : int
        artist id
    name : str
        artist name
    cover : str
        artist cover path
    library_name : str
        artist library name
    """

    id = DB.Column(DB.Text, primary_key=True)
    name = DB.Column(DB.String(255))
    cover = DB.Column(DB.String(255))
    library_name = DB.Column(DB.String(255))

    def __repr__(self) -> str:
        return f"<Artist {self.name}>"


class Album(DB.Model):
    """
    Album model

    ...

    Attributes
    ----------
    artist_id : int
        artist id
    id : int
        album id
    name : str
        album name
    dir_name : str
        album dir name
    cover : str
        album cover path
    tracks : str
        album tracks
    library_name : str
        album library name
    """
    artist_id = DB.Column(DB.Integer, primary_key=True)
    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.String(255))
    dir_name = DB.Column(DB.String(255))
    cover = DB.Column(DB.String(255))
    tracks = DB.Column(DB.Text)
    library_name = DB.Column(DB.String(255))

    def __repr__(self) -> str:
        return f"<Album {self.name}>"


class Track(DB.Model):
    """
    Track model

    ...

    Attributes
    ----------
    artist_id : int
        artist id
    album_id : int
        album id
    id : int
        track id
    name : str
        track name
    slug : str
        track slug
    duration : int
        track duration
    cover: str
        track cover path
    library_name : str
        track library name
    """
    artist_id = DB.Column(DB.Integer)
    album_id = DB.Column(DB.Integer)
    id = DB.Column(DB.Integer, primary_key=True, autoincrement=True)
    name = DB.Column(DB.String(255))
    slug = DB.Column(DB.String(255))
    duration = DB.Column(DB.Integer)
    cover = DB.Column(DB.String(255))
    library_name = DB.Column(DB.String(255))

    def __repr__(self) -> str:
        return f"<Track {self.name}>"


class Playlist(DB.Model):
    """
    Playlist model

    ...

    Attributes
    ----------
    user_id : int
        user id
    id : int
        playlist id
    name : str
        playlist name
    tracks : str
        playlist tracks
    duration : int
        playlist duration
    cover : str
        playlist cover path
    library_name : str
        playlist library name
    """
    user_id = DB.Column(DB.Integer)
    id = DB.Column(DB.Integer, primary_key=True, autoincrement=True)
    name = DB.Column(DB.String(255))
    tracks = DB.Column(DB.Text)
    duration = DB.Column(DB.Integer)
    cover = DB.Column(DB.String(255))
    library_name = DB.Column(DB.String(255))

    def __repr__(self) -> str:
        return f"<Playlist {self.name}>"


class Language(DB.Model):
    language = DB.Column(DB.String(255), primary_key=True)

    def __init__(self, language):
        self.language = language

    def __repr__(self) -> str:
        return f"<Language {self.language}>"


class Actors(DB.Model):
    name = DB.Column(DB.String(255), primary_key=True)
    actor_id = DB.Column(DB.Integer, primary_key=True)
    actor_image = DB.Column(DB.Text)
    actor_description = DB.Column(DB.String(2550))
    actor_birth_date = DB.Column(DB.String(255))
    actor_birth_place = DB.Column(DB.String(255))
    actor_programs = DB.Column(DB.Text)

    def __init__(self, name, actor_id, actor_image, actor_description, actor_birth_date, actor_birth_place, actor_programs):
        self.name = name
        self.actor_id = actor_id
        self.actor_image = actor_image
        self.actor_description = actor_description
        self.actor_birth_date = actor_birth_date
        self.actor_birth_place = actor_birth_place
        self.actor_programs = actor_programs

    def __repr__(self) -> str:
        return f"<Actors {self.name}>"


class Libraries(DB.Model):
    lib_name = DB.Column(DB.String(255), primary_key=True)
    lib_image = DB.Column(DB.String(255))
    lib_type = DB.Column(DB.String(255))
    lib_folder = DB.Column(DB.Text)
    available_for = DB.Column(DB.JSON)

    def __init__(self, lib_name, lib_image, lib_type, lib_folder, available_for):
        self.lib_name = lib_name
        self.lib_image = lib_image
        self.lib_type = lib_type
        self.lib_folder = lib_folder
        self.available_for = available_for

    def __repr__(self) -> str:
        return f"<Libraries {self.lib_name}>"

#une classe qui stocke le nombre de fois qu'a été joué une musique par un utilisateur
class MusicPlayed(DB.Model):
    user_id = DB.Column(DB.Integer, primary_key=True)
    music_id = DB.Column(DB.Integer, primary_key=True)
    play_count = DB.Column(DB.Integer)

    def __init__(self, user_id, music_id, play_count):
        self.user_id = user_id
        self.music_id = music_id
        self.play_count = play_count

    def __repr__(self) -> str:
        return f"<MusicPlayed {self.user_id}>"

#une classe qui stocle les likes d'un utilisateur
class MusicLiked(DB.Model):
    user_id = DB.Column(DB.Integer, primary_key=True)
    music_id = DB.Column(DB.Integer, primary_key=True)
    liked = DB.Column(DB.Integer)
    liked_at = DB.Column(DB.Integer, default=int(time()))

    def __init__(self, user_id, music_id, liked, liked_at):
        self.user_id = user_id
        self.music_id = music_id
        self.liked = liked
        self.liked_at = int(time())

    def __repr__(self) -> str:
        return f"<MusicLiked {self.user_id}>"

class LatestEpisodeWatched(DB.Model):
    user_id = DB.Column(DB.Integer, primary_key=True)
    serie_id = DB.Column(DB.Integer, primary_key=True)
    episode_id = DB.Column(DB.Integer)

    def __init__(self, user_id, serie_id, episode_id):
        self.user_id = user_id
        self.serie_id = serie_id
        self.episode_id = episode_id
    
    def __repr__(self) -> str:
        return f"<LatestEpisodeWatched {self.user_id}>"
