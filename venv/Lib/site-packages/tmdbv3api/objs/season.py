from tmdbv3api.as_obj import AsObj
from tmdbv3api.tmdb import TMDb


class Season(TMDb):
    _urls = {
        "details": "/tv/%s/season/%s",
        "changes": "/tv/season/%s/changes",
        "account_states": "/tv/%s/season/%s/account_states",
        "credits": "/tv/%s/season/%s/credits",
        "external_ids": "/tv/%s/season/%s/external_ids",
        "images": "/tv/%s/season/%s/images",
        "videos": "/tv/%s/season/%s/videos",
    }

    def details(
        self,
        tv_id,
        season_num,
        append_to_response="videos,trailers,images,credits,translations",
    ):
        """
        Get the TV season details by id.
        :param tv_id:
        :param season_num:
        :param append_to_response:
        :return:
        """
        return AsObj(
            **self._call(
                self._urls["details"] % (str(tv_id), str(season_num)),
                "append_to_response=" + append_to_response,
            )
        )

    def changes(
        self, season_id, append_to_response="videos,trailers,images,casts,translations"
    ):
        """
        Get the changes for a TV season. By default only the last 24 hours are returned.
        :param append_to_response: str
        :param season_id: int
        :return:
        """
        return AsObj(
            **self._call(
                self._urls["changes"] % str(season_id),
                "append_to_response=" + append_to_response,
            )
        )

    def account_states(self, tv_id, season_num):
        """
        Get all of the user ratings for the season's episodes.
        :param tv_id:
        :param season_num:
        :return:
        """
        return self._get_obj(
            self._call(
                self._urls["account_states"] % (str(tv_id), str(season_num)), ""
            ),
            None,
        )

    def credits(self, tv_id, season_num):
        """
        Get the credits for TV season.
        :param tv_id:
        :param season_num:
        :return:
        """
        return self._get_obj(
            self._call(self._urls["credits"] % (str(tv_id), str(season_num)), ""),
            None,
        )

    def external_ids(self, tv_id, season_num):
        """
        Get the external ids for a TV season.
        :param tv_id:
        :param season_num:
        :return:
        """
        return self._get_obj(
            self._call(self._urls["external_ids"] % (str(tv_id), str(season_num)), ""),
            None,
        )

    def images(self, tv_id, season_num, page=1):
        """
        Get the images that belong to a TV season.
        :param page:
        :param tv_id:
        :param season_num:
        :return:
        """
        return self._get_obj(
            self._call(
                self._urls["images"] % (str(tv_id), str(season_num)),
                "page=" + str(page),
            ),
            "posters",
        )

    def videos(self, tv_id, season_num, page=1):
        """
        Get the videos that have been added to a TV season.
        :param tv_id:
        :param season_num:
        :param page:
        :return:
        """
        return self._get_obj(
            self._call(
                self._urls["videos"] % (str(tv_id), str(season_num)),
                "page=" + str(page),
            )
        )
