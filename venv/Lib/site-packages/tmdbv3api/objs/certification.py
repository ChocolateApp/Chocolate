from tmdbv3api.tmdb import TMDb
from tmdbv3api.as_obj import AsObj


class Certification(TMDb):
    _urls = {
        "movie_list": "/certification/movie/list",
        "tv_list": "/certification/tv/list",
    }

    def movie_list(self):
        return AsObj(**self._call(self._urls["movie_list"], ""))

    def tv_list(self):
        return AsObj(**self._call(self._urls["tv_list"], ""))
