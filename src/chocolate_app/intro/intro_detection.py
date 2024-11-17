import sqlalchemy
from chocolate_app.tables import Libraries, Series, Seasons, Episodes, RecurringContent
from chocolate_app import create_app
from chocolate_app.intro import rcd
from chocolate_app import DB


class IntroDetector:
    def __init__(self) -> None:
        pass

    def start_library_detection(self, library: Libraries) -> None:
        """
        Start the detection for a library
        """
        series = Series.query.filter_by(library_name=library.name).all()
        for serie in series:
            self.start_series_detection(serie)

    def start_series_detection(self, serie: Series) -> None:
        """
        Start the detection for a series
        """
        seasons = Seasons.query.filter_by(serie=serie.id).all()
        for season in seasons:
            self.start_season_detection(season)

    def start_season_detection(self, season: Seasons) -> None:
        """
        Start the detection for a season
        """
        episodes = Episodes.query.filter_by(season_id=season.season_id).all()
        episodes_ids = [episode.episode_id for episode in episodes]
        allEpisodesScanned = True
        for episode_id in episodes_ids:
            episode_recurring_contents = RecurringContent.query.filter_by(
                episode_id=episode_id
            ).all()
            if not episode_recurring_contents:
                allEpisodesScanned = False
                break
        if allEpisodesScanned:
            return
        episodes_paths = [episode.slug for episode in episodes]
        data = rcd.detect(episodes_paths)
        for key, value in data.items():
            contents = value
            contents.sort(key=lambda x: x[0])
            intro = (0, 0)
            recap = ()
            outro = ()
            episode = Episodes.query.filter_by(slug=key).first()
            episode_id = episode.episode_id

            if len(contents) > 0:
                intro = contents[0]
            if len(contents) > 2:
                recap = contents[1]
            if len(contents) > 1:
                outro = contents[-1]

            if len(recap) > 2 and recap[0] == outro[0] and recap[1] == outro[1]:
                recap = ()

            if len(intro) > 0:
                self.save_recurring_content(intro, "intro", episode_id)
            if len(recap) > 0:
                self.save_recurring_content(recap, "recap", episode_id)
            if len(outro) > 0:
                self.save_recurring_content(outro, "outro", episode_id)

    def save_recurring_content(
        self, content: tuple, content_type: str, episode_id: int
    ) -> None:
        """
        Save the recurring content to the database
        """
        rec = RecurringContent(
            type=content_type,
            start_time=content[0],
            end_time=content[1],
            episode_id=episode_id,
        )
        try:
            DB.session.add(rec)
            DB.session.commit()
        except Exception:
            DB.session.rollback()

def start():
    detector = IntroDetector()
    app = create_app()
    with app.app_context():
        liraries = Libraries.query.filter_by(type="series").all()
        for library in liraries:
            detector.start_library_detection(library)

if __name__ == "__main__":
    start()