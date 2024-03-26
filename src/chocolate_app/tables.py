# Copyright (C) 2024 Impre_visible
from flask_login import UserMixin  # type: ignore
from werkzeug.security import check_password_hash, generate_password_hash
from time import time

from chocolate_app import DB


class Users(DB.Model, UserMixin):  # type: ignore
    """
    Users model

    ...

    Attributes

    ----------

    id : int
    name : str
    password : str
    profil_picture : str
    account_type : str
    """

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
        return f"<User {self.name}>"

    def verify_password(self, pwd):
        if not self.password:
            return True
        return check_password_hash(self.password, pwd)


class Movies(DB.Model):  # type: ignore
    """
    Movies model

    ...

    Attributes
    ----------

    id : int
    title : str
    real_title : str
    cover : str
    banner : str
    slug : str
    description : str
    note : str
    date : str
    genre : str
    duration : str
    cast : str
    bande_annonce_url : str
    adult : str
    library_name : str
    alternatives_names : str
    file_date : float
    """

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


class Series(DB.Model):  # type: ignore
    """
    Series model

    ...

    Attributes
    ----------

    id : int
    name : str
    original_name : str
    genre : str
    duration : str
    description : str
    cast : str
    bande_annonce_url : str
    cover : str
    banner : str
    note : str
    date : str
    serie_modified_time : float
    library_name : str
    adult : str
    """

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


class Seasons(DB.Model):  # type: ignore
    """
    Seasons model

    ...

    Attributes
    ----------

    serie : int
    season_id : int
    season_number : int
    release : str
    episodes_number : str
    season_name : str
    season_description : str
    cover : str
    modified_date : float
    number_of_episode_in_folder : int
    """

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


class Episodes(DB.Model):  # type: ignore
    """
    Episodes model

    ...

    Attributes
    ----------
    season_id : int
    episode_id : int
    episode_name : str
    episode_number : int
    episode_description : str
    episode_cover_path : str
    release_date : str
    slug : str
    """

    season_id = DB.Column(DB.Integer, nullable=False)
    episode_id = DB.Column(DB.Integer, primary_key=True)
    episode_name = DB.Column(DB.String(255), primary_key=True)
    episode_number = DB.Column(DB.Integer, primary_key=True)
    episode_description = DB.Column(DB.Text)
    episode_cover_path = DB.Column(DB.String(255))
    release_date = DB.Column(DB.String(255))
    slug = DB.Column(DB.String(255))

    def __repr__(self) -> str:
        return f"<Episodes {self.season_id} {self.episode_number}>"


class RecurringContent(DB.Model):  # type: ignore
    """
    RecurringContent model for episodes

    ...

    Attributes
    ----------
    episode_id : int
    type: str
    start_time: str
    end_time: str
    """

    episode_id = DB.Column(DB.Integer, primary_key=True)
    type = DB.Column(DB.String(255), primary_key=True)
    start_time = DB.Column(DB.String(255), primary_key=True)
    end_time = DB.Column(DB.String(255), primary_key=True)

    def __repr__(self) -> str:
        return f"<RecurringContent {self.episode_id} {self.type}>"


class Games(DB.Model):  # type: ignore
    """
    Games model

    ...

    Attributes
    ----------
    console : str
    id : int
    title : str
    real_title : str
    cover : str
    description : str
    note : str
    date : str
    genre : str
    slug : str
    library_name : str
    """

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


class OthersVideos(DB.Model):  # type: ignore
    """
    OthersVideos model

    ...

    Attributes
    ----------
    video_hash : str
    title : str
    slug : str
    banner : str
    duration : str
    library_name : str
    """

    video_hash = DB.Column(DB.String(255), primary_key=True)
    title = DB.Column(DB.String(255), primary_key=True)
    slug = DB.Column(DB.String(255))
    banner = DB.Column(DB.String(255))
    duration = DB.Column(DB.String(255))
    library_name = DB.Column(DB.String(255))

    def __repr__(self) -> str:
        return f"<OthersVideos {self.title}>"


class Books(DB.Model):  # type: ignore
    """
    Books model

    ...

    Attributes
    ----------
    id : int
    title : str
    slug : str
    book_type : str
    cover : str
    library_name : str
    """

    id = DB.Column(DB.Integer, primary_key=True, autoincrement=True)
    title = DB.Column(DB.String(255))
    slug = DB.Column(DB.String(255))
    book_type = DB.Column(DB.String(255))
    cover = DB.Column(DB.String(255))
    library_name = DB.Column(DB.String(255))

    def __repr__(self) -> str:
        return f"<Books {self.title}>"


class Artists(DB.Model):  # type: ignore
    """
    Artists model

    ...

    Attributes
    ----------
    id : int
    name : str
    cover : str
    library_name : str
    """

    id = DB.Column(DB.Text, primary_key=True)
    name = DB.Column(DB.String(255))
    cover = DB.Column(DB.String(255))
    library_name = DB.Column(DB.String(255))

    def __repr__(self) -> str:
        return f"<Artists {self.name}>"


class Albums(DB.Model):  # type: ignore
    """
    Albums model

    ...

    Attributes
    ----------
    artist_id : int
    id : int
    name : str
    dir_name : str
    cover : str
    tracks : str
    library_name : str
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


class Tracks(DB.Model):  # type: ignore
    """
    Tracks model

    ...

    Attributes
    ----------
    artist_id : int
    album_id : int
    id : int
    name : str
    slug : str
    duration : int
    cover: str
    library_name : str
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


class Playlists(DB.Model):  # type: ignore
    """
    Playlist model

    ...

    Attributes
    ----------
    user_id : int
    id : int
    name : str
    tracks : str
    duration : int
    cover : str
    library_name : str
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


class Language(DB.Model):  # type: ignore
    """
    Language model

    ...

    Attributes
    ----------
    language : str
    """

    language = DB.Column(DB.String(255), primary_key=True)

    def __repr__(self) -> str:
        return f"<Language {self.language}>"


class Actors(DB.Model):  # type: ignore
    """
    Actors model

    ...

    Attributes
    ----------
    name : str
    actor_id : int
    actor_image : str
    actor_description : str
    actor_birth_date : str
    actor_birth_place : str
    actor_programs : str
    """

    name = DB.Column(DB.String(255), primary_key=True)
    actor_id = DB.Column(DB.Integer, primary_key=True)
    actor_image = DB.Column(DB.Text)
    actor_description = DB.Column(DB.String(2550))
    actor_birth_date = DB.Column(DB.String(255))
    actor_birth_place = DB.Column(DB.String(255))
    actor_programs = DB.Column(DB.Text)

    def __repr__(self) -> str:
        return f"<Actors {self.name}>"


class Libraries(DB.Model):  # type: ignore
    """
    Libraries model

    ...

    Attributes
    ----------
    lib_name : str
    lib_image : str
    lib_type : str
    lib_folder : str
    available_for : str
    """

    lib_name = DB.Column(DB.Text, primary_key=True)
    lib_image = DB.Column(DB.Text)
    lib_type = DB.Column(DB.Text)
    lib_folder = DB.Column(DB.Text)
    available_for = DB.Column(DB.Text)

    def __repr__(self) -> str:
        return f"<Libraries {self.lib_name}>"


class MusicPlayed(DB.Model):  # type: ignore
    """
    MusicPlayed model

    ...

    Attributes
    ----------
    user_id : int
    music_id : int
    play_count : int
    """

    user_id = DB.Column(DB.Integer, primary_key=True)
    music_id = DB.Column(DB.Integer, primary_key=True)
    play_count = DB.Column(DB.Integer)

    def __repr__(self) -> str:
        return f"<MusicPlayed {self.user_id}>"


class MusicLiked(DB.Model):  # type: ignore
    """
    MusicLiked model

    ...

    Attributes
    ----------
    user_id : int
    music_id : int
    liked : int
    liked_at : int
    """

    user_id = DB.Column(DB.Integer, primary_key=True)
    music_id = DB.Column(DB.Integer, primary_key=True)
    liked = DB.Column(DB.Integer)
    liked_at = DB.Column(DB.Integer, default=int(time()))

    def __repr__(self) -> str:
        return f"<MusicLiked {self.user_id}>"


class LatestEpisodeWatched(DB.Model):  # type: ignore
    """
    LatestEpisodeWatched model

    ...

    Attributes
    ----------
    user_id : int
    serie_id : int
    episode_id : int
    """

    user_id = DB.Column(DB.Integer, primary_key=True)
    serie_id = DB.Column(DB.Integer, primary_key=True)
    episode_id = DB.Column(DB.Integer)

    def __repr__(self) -> str:
        return f"<LatestEpisodeWatched {self.user_id}>"


class InviteCodes(DB.Model):  # type: ignore
    """
    InviteCodes model

    ...

    Attributes
    ----------
    code : str
    """

    code = DB.Column(DB.String(255), primary_key=True)

    def __repr__(self) -> str:
        return f"<InviteCode {self.code}>"


class LibrariesMerge(DB.Model):  # type: ignore
    """
    LibrariesMerge model

    ...

    Attributes
    ----------
    parent_lib : str
    child_lib : str
    """

    parent_lib = DB.Column(DB.String(255), primary_key=True)
    child_lib = DB.Column(DB.String(255), primary_key=True)

    def __repr__(self) -> str:
        return f"<LibrariesMerge {self.parent_lib}>"
