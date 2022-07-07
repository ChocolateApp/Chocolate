import os

from tmdbv3api.as_obj import AsObj
from tmdbv3api.exceptions import TMDbException
from tmdbv3api.tmdb import TMDb


class Account(TMDb):
    _urls = {
        "details": "/account",
        "watchlist": "/account/%s/watchlist",
    }

    def details(self):
        return AsObj(
            **self._call(
                self._urls["details"],
                "session_id=%s" % os.environ.get("TMDB_SESSION_ID"),
            )
        )

    def add_to_watchlist(self, account_id, media_id, media_type):
        if media_type not in ["tv", "movie"]:
            raise TMDbException("Media Type should be tv or movie.")
        return self._get_obj(
            self._call(
                self._urls["watchlist"] % account_id,
                "session_id=%s" % os.environ.get("TMDB_SESSION_ID"),
                method="POST",
                data={
                    "media_type": media_type,
                    "media_id": media_id,
                    "watchlist": True,
                },
            ),
            None,
        )
