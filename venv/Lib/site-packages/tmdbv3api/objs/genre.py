from tmdbv3api.tmdb import TMDb


class Genre(TMDb):
    _urls = {"movie_list": "/genre/movie/list", "tv_list": "/genre/tv/list"}

    def movie_list(self):
        return self._get_obj(self._call(self._urls["movie_list"], ""), key="genres")

    def tv_list(self):
        return self._get_obj(self._call(self._urls["tv_list"], ""), key="genres")
