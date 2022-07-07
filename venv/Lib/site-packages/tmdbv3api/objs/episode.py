from tmdbv3api.as_obj import AsObj
from tmdbv3api.tmdb import TMDb


class Episode(TMDb):
    _urls = {
        "details": "/tv/%s/season/%s/episode/%s",
        "external_ids": "/tv/%s/season/%s/episode/%s/external_ids",
    }

    def details(
        self,
        tv_id,
        season_num,
        episode_num,
        append_to_response="trailers,images,casts,translations",
    ):
        return AsObj(
            **self._call(
                self._urls["details"] % (str(tv_id), str(season_num), str(episode_num)),
                "append_to_response=%s" % append_to_response,
            )
        )

    def external_ids(self, tv_id, season_num, episode_num):
        """
        Get the external ids for a TV episode.
        :param tv_id:
        :param season_num:
        :param episode_num:
        :return:
        """
        return self._get_obj(
            self._call(
                self._urls["external_ids"]
                % (str(tv_id), str(season_num), str(episode_num)),
                "",
            ),
            None,
        )
