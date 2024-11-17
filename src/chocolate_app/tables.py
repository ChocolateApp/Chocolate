# Copyright (C) 2024 Impre_visible
from time import time
from flask_login import UserMixin  # type: ignore
from werkzeug.security import check_password_hash, generate_password_hash

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
    profile_picture : str
    account_type : str
    """

    id = DB.Column(DB.Integer, autoincrement=True, primary_key=True)
    name = DB.Column(DB.String(255), unique=True)
    password = DB.Column(DB.String(255))
    profile_picture = DB.Column(DB.String(255))
    account_type = DB.Column(DB.String(255))

    def __init__(self, name, password, profile_picture, account_type):
        self.name = name
        if password is not None and password != "":
            self.password = generate_password_hash(password)
        else:
            self.password = None
        self.profile_picture = profile_picture
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
    tmdb_id : int
    title : str
    cover : str
    banner : str
    logo : str
    cover_b64 : str
    banner_b64 : str
    logo_b64 : str
    slug : str
    description : str
    note : str
    date : str
    genre : str
    duration : str
    cast : str
    adult : str
    library_name : str
    alternative_title : str
    file_date : float
    """

    id = DB.Column(DB.Integer, autoincrement=True, primary_key=True)
    tmdb_id = DB.Column(DB.Integer)
    title = DB.Column(DB.String(255))
    cover = DB.Column(DB.String(255))
    banner = DB.Column(DB.String(255))
    logo = DB.Column(DB.String(255))
    cover_b64 = DB.Column(DB.Text)
    banner_b64 = DB.Column(DB.Text)
    logo_b64 = DB.Column(DB.Text)
    slug = DB.Column(DB.String(255))
    description = DB.Column(DB.String(2550))
    note = DB.Column(DB.String(255))
    date = DB.Column(DB.String(255))
    genre = DB.Column(DB.String(255))
    duration = DB.Column(DB.String(255))
    cast = DB.Column(DB.String(255))
    adult = DB.Column(DB.String(255))
    library_name = DB.Column(DB.String(255))
    alternative_title = DB.Column(DB.Text)
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
    tmdb_id : int
    title : str
    genre : str
    duration : str
    description : str
    cast : str
    trailer_url : str
    cover : str
    banner : str
    logo : str
    cover_b64 : str
    banner_b64 : str
    logo_b64 : str
    note : str
    date : str
    serie_modified_time : float
    library_name : str
    adult : str
    """

    id = DB.Column(DB.Integer, autoincrement=True, primary_key=True)
    tmdb_id = DB.Column(DB.Integer)
    path = DB.Column(DB.String(255), nullable=False)
    title = DB.Column(DB.String(255))
    genre = DB.Column(DB.String(255))
    duration = DB.Column(DB.String(255))
    description = DB.Column(DB.String(2550))
    cast = DB.Column(DB.String(255))
    trailer_url = DB.Column(DB.String(255))
    cover = DB.Column(DB.String(255))
    banner = DB.Column(DB.String(255))
    logo = DB.Column(DB.String(255))
    cover_b64 = DB.Column(DB.Text)
    banner_b64 = DB.Column(DB.Text)
    logo_b64 = DB.Column(DB.Text)
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

    id : int
    tmdb_id : int
    serie_id : int
    number : int
    release : str
    episodes_number : str
    title : str
    description : str
    cover : str
    modified_date : float
    number_of_episode_in_folder : int
    """

    id = DB.Column(DB.Integer, autoincrement=True, primary_key=True)
    tmdb_id = DB.Column(DB.Integer)
    serie_id = DB.Column(DB.Integer, nullable=False)
    number = DB.Column(DB.Integer)
    release = DB.Column(DB.String(255))
    episodes_number = DB.Column(DB.String(255))
    title = DB.Column(DB.String(255))
    description = DB.Column(DB.Text)
    cover = DB.Column(DB.String(255))
    modified_date = DB.Column(DB.Float)
    number_of_episode_in_folder = DB.Column(DB.Integer)

    def __repr__(self) -> str:
        return f"<Seasons {self.serie_id} {self.id}>"


class Episodes(DB.Model):  # type: ignore
    """
    Episodes model

    ...

    Attributes
    ----------
    id : int
    tmdb_id : int
    serie_id : int
    season_id : int
    title : str
    number : int
    description : str
    cover_path : str
    cover_b64 : str
    release_date : str
    slug : str
    """

    id = DB.Column(DB.Integer, autoincrement=True, primary_key=True)
    tmdb_id = DB.Column(DB.Integer)
    serie_id = DB.Column(DB.Integer, nullable=False)
    season_id = DB.Column(DB.Integer, nullable=False)
    title = DB.Column(DB.String(255))
    number = DB.Column(DB.Integer)
    description = DB.Column(DB.Text)
    cover_path = DB.Column(DB.String(255))
    cover_b64 = DB.Column(DB.Text)
    release_date = DB.Column(DB.String(255))
    slug = DB.Column(DB.String(255))

    def __repr__(self) -> str:
        return f"<Episodes {self.season_id} {self.id}>"


class RecurringContent(DB.Model):  # type: ignore
    """
    RecurringContent model for episodes

    ...

    Attributes
    ----------
    id : int
    episode_id : int
    type: str
    start_time: str
    end_time: str
    """

    id = DB.Column(DB.Integer, autoincrement=True, primary_key=True)
    episode_id = DB.Column(DB.Integer)
    type = DB.Column(DB.String(255))
    start_time = DB.Column(DB.String(255))
    end_time = DB.Column(DB.String(255))

    def __repr__(self) -> str:
        return f"<RecurringContent {self.episode_id} {self.type}>"


class TVChannels(DB.Model):  # type: ignore
    """
    TVChannels model

    ...

    Attributes
    ----------
    id : int
    lib_id : int
    name : str
    logo : str
    slug : str
    """

    id = DB.Column(DB.Integer, autoincrement=True, primary_key=True)
    lib_id = DB.Column(DB.Integer)
    name = DB.Column(DB.String(255))
    logo = DB.Column(DB.String(255))
    slug = DB.Column(DB.String(255))

    def __repr__(self) -> str:
        return f"<TVChannels {self.name}>"


class TVPrograms(DB.Model):  # type: ignore
    """
    TVPrograms model

    ...

    Attributes
    ----------
    id : int
    channel_id : int
    title : str
    start_time : datetime
    end_time : datetime
    cover : str
    """

    id = DB.Column(DB.Integer, autoincrement=True, primary_key=True)
    channel_id = DB.Column(DB.Integer)
    title = DB.Column(DB.String(255))
    start_time = DB.Column(DB.String(255))
    end_time = DB.Column(DB.String(255))
    cover = DB.Column(DB.String(255))

    def __repr__(self) -> str:
        return f"<TVPrograms {self.title}>"


class Games(DB.Model):  # type: ignore
    # TODO: Rework this model to have a better structure
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
    cover_b64 : str
    description : str
    note : str
    date : str
    genre : str
    slug : str
    library_name : str
    """

    console = DB.Column(DB.String(255), primary_key=True)
    id = DB.Column(DB.Integer)
    title = DB.Column(DB.String(255))
    real_title = DB.Column(DB.String(255))
    cover = DB.Column(DB.String(255))
    cover_b64 = DB.Column(DB.Text)
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
    id: int
    title : str
    slug : str
    banner : str
    banner_b64 : str
    duration : str
    library_name : str
    """

    id = DB.Column(DB.Integer, autoincrement=True, primary_key=True)
    title = DB.Column(DB.String(255))
    slug = DB.Column(DB.String(255))
    banner = DB.Column(DB.String(255))
    banner_b64 = DB.Column(DB.Text)
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
    cover_b64 : str
    library_name : str
    """

    id = DB.Column(DB.Integer, autoincrement=True, primary_key=True)
    title = DB.Column(DB.String(255))
    slug = DB.Column(DB.String(255))
    book_type = DB.Column(DB.String(255))
    cover = DB.Column(DB.String(255))
    cover_b64 = DB.Column(DB.Text)
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
    id : int
    artist_id : int
    title : str
    dir_name : str
    cover : str
    cover_b64 : str
    tracks : str
    library_name : str
    release_date : str
    note : str
    """

    id = DB.Column(DB.Integer, autoincrement=True, primary_key=True)
    artist_id = DB.Column(DB.Integer)
    title = DB.Column(DB.String(255))
    dir_name = DB.Column(DB.String(255))
    cover = DB.Column(DB.String(255))
    cover_b64 = DB.Column(DB.Text)
    tracks = DB.Column(DB.Text)
    library_name = DB.Column(DB.String(255))
    release_date = DB.Column(DB.String(255))
    note = DB.Column(DB.String(255))

    def __repr__(self) -> str:
        return f"<Albums {self.title}>"


class Tracks(DB.Model):  # type: ignore
    """
    Tracks model

    ...

    Attributes
    ----------
    artist_id : int
    album_id : int
    id : int
    title : str
    slug : str
    duration : int
    cover: str
    cover_b64 : str
    library_name : str
    """

    id = DB.Column(DB.Integer, autoincrement=True, primary_key=True)
    artist_id = DB.Column(DB.Integer)
    album_id = DB.Column(DB.Integer)
    title = DB.Column(DB.String(255))
    slug = DB.Column(DB.String(255))
    duration = DB.Column(DB.Integer)
    cover = DB.Column(DB.String(255))
    cover_b64 = DB.Column(DB.Text)
    library_name = DB.Column(DB.String(255))
    file_date = DB.Column(DB.Float)
    release_date = DB.Column(DB.String(255))

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
    title : str
    tracks : str
    duration : int
    cover : str
    library_name : str
    """

    id = DB.Column(DB.Integer, autoincrement=True, primary_key=True)
    user_id = DB.Column(DB.Integer)
    title = DB.Column(DB.String(255))
    tracks = DB.Column(DB.Text)
    duration = DB.Column(DB.Integer)
    cover = DB.Column(DB.String(255))
    library_name = DB.Column(DB.String(255))

    def __repr__(self) -> str:
        return f"<Playlist {self.title}>"


class Language(DB.Model):  # type: ignore
    """
    Language model

    ...

    Attributes
    ----------
    id : int
    language : str

    """

    id = DB.Column(DB.Integer, autoincrement=True, primary_key=True)
    language = DB.Column(DB.String(255))

    def __repr__(self) -> str:
        return f"<Language {self.language}>"


class Actors(DB.Model):  # type: ignore
    """
    Actors model

    ...

    Attributes
    ----------
    id : int
    name : str
    image : str
    image_b64 : str
    description : str
    birth_date : str
    birth_place : str
    programs : str
    """

    id = DB.Column(DB.Integer, autoincrement=True, primary_key=True)
    tmdb_id = DB.Column(DB.Integer)
    name = DB.Column(DB.String(255))
    image = DB.Column(DB.Text)
    image_b64 = DB.Column(DB.Text)
    description = DB.Column(DB.String(2550))
    birth_date = DB.Column(DB.String(255))
    birth_place = DB.Column(DB.String(255))
    programs = DB.Column(DB.Text)

    def __repr__(self) -> str:
        return f"<Actors {self.name}>"


class Libraries(DB.Model):  # type: ignore
    """
    Libraries model

    ...

    Attributes
    ----------
    id : int
    name : str
    image : str
    type : str
    folder : str
    available_for : str
    """

    id = DB.Column(DB.Integer, autoincrement=True, primary_key=True)
    name = DB.Column(DB.Text)
    image = DB.Column(DB.Text)
    type = DB.Column(DB.Text)
    folder = DB.Column(DB.Text)
    available_for = DB.Column(DB.Text)

    def __init__(self, name, image, type, folder, available_for):
        self.name = name
        self.image = image
        self.type = type
        self.folder = folder
        self.available_for = available_for

    def __repr__(self) -> str:
        return f"<Libraries {self.name}>"


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


class MediaPlayed(DB.Model):  # type: ignore
    """
    MediaPlayed model

    This table is used to store the media played by the users,
    to have a history of the media played,
    be able to continue the media where the user stopped,
    and to have statistics on the media

    ...

    Attributes
    ----------
    id : int
    user_id : int
    media_type : str
    media_id : int
    season_id : int | None
    serie_id : int | None
    datetime : datetime
    duration : int
    """

    id = DB.Column(DB.Integer, autoincrement=True, primary_key=True)
    user_id = DB.Column(DB.Integer)
    media_type = DB.Column(DB.String(255))
    media_id = DB.Column(DB.Integer)
    season_id = DB.Column(DB.Integer, nullable=True)
    serie_id = DB.Column(DB.Integer, nullable=True)
    datetime = DB.Column(DB.Text)
    duration = DB.Column(DB.Integer)

    def __repr__(self) -> str:
        return f"<MediaPlayed {self.id}>"


class InviteCodes(DB.Model):  # type: ignore
    """
    InviteCodes model

    ...

    Attributes
    ----------
    code : str
    """

    id = DB.Column(DB.Integer, autoincrement=True, primary_key=True)
    code = DB.Column(DB.String(255))

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

    id = DB.Column(DB.Integer, autoincrement=True, primary_key=True)
    parent_lib = DB.Column(DB.String(255))
    child_lib = DB.Column(DB.String(255))

    def __repr__(self) -> str:
        return f"<LibrariesMerge {self.parent_lib}>"
