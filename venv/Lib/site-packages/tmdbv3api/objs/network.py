from tmdbv3api.tmdb import TMDb
from tmdbv3api.as_obj import AsObj


class Network(TMDb):
    _urls = {"details": "/network/%s"}

    def details(self, network_id):
        """
        Get a networks details by id.
        :param network_id: int
        :return:
        """
        return AsObj(**self._call(self._urls["details"] % str(network_id), ""))
