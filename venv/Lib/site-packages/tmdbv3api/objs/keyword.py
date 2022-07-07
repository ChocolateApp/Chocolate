from tmdbv3api.tmdb import TMDb
from tmdbv3api.as_obj import AsObj


class Keyword(TMDb):
    _urls = {"details": "/keyword/%s", "movies": "/keyword/%s/movies"}

    def details(self, keyword_id):
        """
        Get a keywords details by id.
        :param keyword_id: int
        :return:
        """
        return AsObj(**self._call(self._urls["details"] % str(keyword_id), ""))

    def movies(self, keyword_id):
        """
        Get the movies of a keyword by id.
        :param keyword_id: int
        :return:
        """
        return self._get_obj(self._call(self._urls["movies"] % str(keyword_id), ""))
