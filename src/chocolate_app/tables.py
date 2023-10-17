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
        if password is not None and password != "":
            self.password = generate_password_hash(password)
        else:
            self.password = None
        self.profil_picture = profil_picture
        self.account_type = account_type

    def __repr__(self) -> str:
        return f"<Name {self.name}>"

    def verify_password(self, pwd):
        if not self.password:
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
    file_date = DB.Column(DB.Float)

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
    cover = DB.Column(DB.String(255))
    banner = DB.Column(DB.String(255))
    note = DB.Column(DB.String(255))
    date = DB.Column(DB.String(255))
    serie_modified_time = DB.Column(DB.Float)
    library_name = DB.Column(DB.String(255))
    adult = DB.Column(DB.String(255))

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
    cover = DB.Column(DB.String(255))
    modified_date = DB.Column(DB.Float)
    number_of_episode_in_folder = DB.Column(DB.Integer)

    def __repr__(self) -> str:
        return f"<Seasons {self.serie} {self.season_id}>"


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

    def __repr__(self) -> str:
        return f"<Episodes {self.season_id} {self.episode_number}>"


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

    def __repr__(self) -> str:
        return f"<Games {self.title}>"


class OthersVideos(DB.Model):
    video_hash = DB.Column(DB.String(255), primary_key=True)
    title = DB.Column(DB.String(255), primary_key=True)
    slug = DB.Column(DB.String(255))
    banner = DB.Column(DB.String(255))
    duration = DB.Column(DB.String(255))
    library_name = DB.Column(DB.String(255))

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


class Artists(DB.Model):
    """
    Artists model

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
        return f"<Artists {self.name}>"


class Albums(DB.Model):
    """
    Albums model

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
        return f"<Albums {self.name}>"


class Tracks(DB.Model):
    """
    Tracks model

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
        return f"<Tracks {self.name}>"


class Playlists(DB.Model):
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

    def __repr__(self) -> str:
        return f"<Actors {self.name}>"


class Libraries(DB.Model):
    lib_name = DB.Column(DB.Text, primary_key=True)
    lib_image = DB.Column(DB.Text)
    lib_type = DB.Column(DB.Text)
    lib_folder = DB.Column(DB.Text)
    available_for = DB.Column(DB.Text)

    def __repr__(self) -> str:
        return f"<Libraries {self.lib_name}>"


# une classe qui stocke le nombre de fois qu'a été joué une musique par un utilisateur
class MusicPlayed(DB.Model):
    user_id = DB.Column(DB.Integer, primary_key=True)
    music_id = DB.Column(DB.Integer, primary_key=True)
    play_count = DB.Column(DB.Integer)

    def __repr__(self) -> str:
        return f"<MusicPlayed {self.user_id}>"


# une classe qui stocle les likes d'un utilisateur
class MusicLiked(DB.Model):
    user_id = DB.Column(DB.Integer, primary_key=True)
    music_id = DB.Column(DB.Integer, primary_key=True)
    liked = DB.Column(DB.Integer)
    liked_at = DB.Column(DB.Integer, default=int(time()))

    def __repr__(self) -> str:
        return f"<MusicLiked {self.user_id}>"


class LatestEpisodeWatched(DB.Model):
    user_id = DB.Column(DB.Integer, primary_key=True)
    serie_id = DB.Column(DB.Integer, primary_key=True)
    episode_id = DB.Column(DB.Integer)

    def __repr__(self) -> str:
        return f"<LatestEpisodeWatched {self.user_id}>"


class InviteCodes(DB.Model):
    code = DB.Column(DB.String(255), primary_key=True)

    def __repr__(self) -> str:
        return f"<InviteCode {self.code}>"


class LibrariesMerge(DB.Model):
    parent_lib = DB.Column(DB.String(255), primary_key=True)
    child_lib = DB.Column(DB.String(255), primary_key=True)

    def __repr__(self) -> str:
        return f"<LibrariesMerge {self.parent_lib}>"
