from tmdbv3api.tmdb import TMDb
from tmdbv3api.as_obj import AsObj


class Configuration(TMDb):
    _urls = {
        "info": "/configuration",
        "countries": "/configuration/countries",
        "jobs": "/configuration/jobs",
        "languages": "/configuration/languages",
        "primary_translations": "/configuration/primary_translations",
        "timezones": "/configuration/timezones"
        }

    def info(self):
        """
        Get the system wide configuration info.
        """
        return AsObj(**self._call(self._urls["info"], ""))

    def countries(self):
        """
        Get the list of countries (ISO 3166-1 tags) used throughout TMDb.
        """
        return self._call(self._urls["countries"], "")

    def jobs(self):
        """
        Get a list of the jobs and departments we use on TMDb.
        """
        return self._call(self._urls["jobs"], "")

    def languages(self):
        """
        Get the list of languages (ISO 639-1 tags) used throughout TMDb.
        """
        return self._call(self._urls["languages"], "")

    def primary_translations(self):
        """
        Get a list of the officially supported translations on TMDb.
        """
        return self._call(self._urls["primary_translations"], "")

    def timezones(self):
        """
        Get the list of timezones used throughout TMDb.
        """
        return self._call(self._urls["timezones"], "")
