from tmdbv3api.as_obj import AsObj
from tmdbv3api.tmdb import TMDb


class Collection(TMDb):
    _urls = {
        "details": "/collection/%s",
        "images": "/collection/%s/images", 
        "translations": "/collection/%s/translations"
        }

    def details(self, collection_id):
        """
        Get collection details by id.
        :param collection_id:
        :return:
        """
        return AsObj(**self._call(self._urls["details"] % str(collection_id), ""))

    def images(self, collection_id):
        """
        Get the images for a collection by id.
        :param collection_id:
        :return:
        """
        return AsObj(**self._call(self._urls["images"] % str(collection_id), ""))

    def translations(self, collection_id):
        """
        Get the list translations for a collection by id.
        :param collection_id:
        :return:
        """
        return self._get_obj(self._call(self._urls["translations"] % str(collection_id), ""), "translations")