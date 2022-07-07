from tmdbv3api.tmdb import TMDb

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode


class Discover(TMDb):
    _urls = {"movies": "/discover/movie", "tv": "/discover/tv"}

    def discover_movies(self, params):
        """
        Discover movies by different types of data like average rating, number of votes, genres and certifications.
        :param params:
        :return:
        """
        return self._get_obj(self._call(self._urls["movies"], urlencode(params)))

    def discover_tv_shows(self, params):
        """
        Discover TV shows by different types of data like average rating, number of votes, genres,
        the network they aired on and air dates.
        :param params:
        :return:
        """
        return self._get_obj(self._call(self._urls["tv"], urlencode(params)))
