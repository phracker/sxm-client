import datetime
import time
from dataclasses import dataclass
from typing import List, Optional, Union

__all__ = [
    'XMArt', 'XMImage', 'XMCategory', 'XMMarker', 'XMShow',
    'XMEpisode', 'XMEpisodeMarker', 'XMArtist', 'XMAlbum',
    'XMCut', 'XMSong', 'XMCutMarker', 'XMPosition', 'XMHLSInfo',
    'XMChannel', 'XMLiveChannel',
]


LIVE_PRIMARY_HLS = 'https://siriusxm-priprodlive.akamaized.net'


class XMArt:
    name: Optional[str]
    url: str
    art_type: str

    def __init__(self, art_dict: dict):
        self.name = art_dict.get('name', None)
        self.url = art_dict['url']
        self.art_type = art_dict['type']


class XMImage(XMArt):
    platform: Optional[str] = None
    height: Optional[int] = None
    width: Optional[int] = None
    size: Optional[str] = None

    def __init__(self, image_dict: dict):
        image_dict['type'] = 'IMAGE'
        super().__init__(image_dict)

        self.platform = image_dict.get('platform', None)
        self.height = image_dict.get('height', None)
        self.width = image_dict.get('width', None)
        self.size = image_dict.get('size', None)


class XMCategory:
    guid: str
    name: str
    key: str
    is_primary: bool = True

    def __init__(self, category_dict: dict):
        self.guid = category_dict['categoryGuid']
        self.name = category_dict['name']
        self.key = category_dict['key']
        self.is_primary = category_dict['isPrimary']


class XMMarker:
    guid: str
    time: int
    duration: int

    def __init__(self, marker_dict: dict):
        self.guid = marker_dict['assetGUID']
        self.time = marker_dict['time']
        self.duration = marker_dict['duration']


class XMShow:
    guid: str
    medium_title: str
    long_title: str
    short_description: str
    long_description: str
    arts: List[XMArt]
    # ... plus many unused

    def __init__(self, show_dict: dict):
        self.guid = show_dict['showGUID']
        self.medium_title = show_dict['mediumTitle']
        self.long_title = show_dict['longTitle']
        self.short_description = show_dict['shortDescription']
        self.long_description = show_dict['longDescription']

        self.arts = []
        for art in show_dict.get('creativeArts', []):
            if art['type'] == 'IMAGE':
                self.arts.append(XMImage(art))


class XMEpisode:
    guid: str
    medium_title: str
    long_title: str
    short_description: str
    long_description: str
    show: XMShow
    # ... plus many unused

    def __init__(self, episode_dict: dict):
        self.guid = episode_dict['episodeGUID']
        self.medium_title = episode_dict['mediumTitle']
        self.long_title = episode_dict['longTitle']
        self.short_description = episode_dict['shortDescription']
        self.long_description = episode_dict['longDescription']
        self.show = XMShow(episode_dict['show'])


class XMEpisodeMarker(XMMarker):
    episode: XMEpisode

    def __init__(self, marker_dict: dict):
        super().__init__(marker_dict)

        self.episode = XMEpisode(marker_dict['episode'])


class XMArtist:
    name: str

    def __init__(self, artist_dict: dict):
        self.name = artist_dict['name']


class XMAlbum:
    title: Optional[str] = None
    arts: List[XMArt]

    def __init__(self, album_dict: dict):
        self.title = album_dict.get('title', None)

        self.arts = []
        for art in album_dict.get('creativeArts', []):
            if art['type'] == 'IMAGE':
                self.arts.append(XMImage(art))


class XMCut:
    title: str
    artists: List[XMArtist]
    cut_type: Optional[str] = None

    def __init__(self, cut_dict: dict):
        self.title = cut_dict['title']
        self.cut_type = cut_dict.get('cutContentType', None)

        self.artists = []
        for artist in cut_dict['artists']:
            self.artists.append(XMArtist(artist))


class XMSong(XMCut):
    album: Optional[XMAlbum] = None
    itunes_id: Optional[str] = None

    def __init__(self, song_dict: dict):
        super().__init__(song_dict)

        if 'album' in song_dict:
            self.album = XMAlbum(song_dict['album'])

        for external_id in song_dict.get('externalIds', []):
            if external_id['id'] == 'iTunes':
                self.itunes_id = external_id['value']


class XMCutMarker(XMMarker):
    cut: XMCut

    def __init__(self, marker_dict: dict):
        super().__init__(marker_dict)

        if marker_dict['cut'].get('cutContentType', None) == 'Song':
            self.cut = XMSong(marker_dict['cut'])
        else:
            self.cut = XMCut(marker_dict['cut'])
        # other cuts, not done: Exp, Link., maybe more?


class XMPosition:
    timestamp: datetime.datetime
    position: str

    def __init__(self, pos_dict: dict):
        dt_string = pos_dict['timestamp'].replace('+0000', '')
        dt = datetime.datetime.fromisoformat(dt_string)

        self.timestamp = dt.replace(tzinfo=datetime.timezone.utc)
        self.position = pos_dict['position']


class XMHLSInfo:
    name: str
    url: str
    size: str
    position: Optional[XMPosition] = None
    # + unused chunks

    def __init__(self, hls_dict: dict):
        self.name = hls_dict['name']
        self.url = hls_dict['url'].replace(
            '%Live_Primary_HLS%', LIVE_PRIMARY_HLS)
        self.size = hls_dict['size']

        if 'position' in hls_dict:
            self.position = XMPosition(hls_dict['position'])


class XMChannel:
    """See `tests/sample_data/xm_channel.json` for sample"""
    guid: str
    id: str
    name: str
    streaming_name: str
    sort_order: int
    short_description: str
    medium_description: str
    url: str
    is_available: bool
    is_favorite: bool
    is_mature: bool
    channel_number: int  # actually siriusChannelNumber
    images: List[XMImage]
    categories: List[XMCategory]
    # ... plus many unused

    def __init__(self, channel_dict: dict):
        self.guid = channel_dict['channelGuid']
        self.id = channel_dict['channelId']
        self.name = channel_dict['name']
        self.streaming_name = channel_dict['streamingName']
        self.sort_order = channel_dict['sortOrder']
        self.short_description = channel_dict['shortDescription']
        self.medium_description = channel_dict['mediumDescription']
        self.url = channel_dict['url']
        self.is_available = channel_dict['isAvailable']
        self.is_favorite = channel_dict['isFavorite']
        self.is_mature = channel_dict['isMature']
        self.channel_number = channel_dict['siriusChannelNumber']

        self.images = []
        for image in channel_dict['images']['images']:
            self.images.append(XMImage(image))

        self.categories = []
        for category in channel_dict['categories']['categories']:
            self.categories.append(XMCategory(category))

    @property
    def pretty_name(self) -> str:
        """ Returns a formated version of channel number + channel name """
        return f'#{self.channel_number} {self.name}'


@dataclass
class XMLiveChannel:
    """See `tests/sample_data/xm_live_channel.json` for sample"""

    id: str
    hls_infos: List[XMHLSInfo]
    custom_hls_infos: List[XMHLSInfo]
    episode_markers: List[XMEpisodeMarker]
    cut_markers: List[XMCutMarker]
    _song_cuts: Optional[List[XMCutMarker]] = None
    tune_time: Optional[int] = None
    # ... plus many unused

    def __init__(self, live_dict: dict):
        self.id = live_dict['channelId']

        self.hls_infos = []
        self.custom_hls_infos = []
        self.episode_markers = []
        self.cut_markers = []

        for info in live_dict['hlsAudioInfos']:
            self.hls_infos.append(XMHLSInfo(info))

        for info in live_dict['customAudioInfos']:
            self.custom_hls_infos.append(XMHLSInfo(info))

        for hls_info in self.custom_hls_infos:
            if hls_info.position is not None and \
                    hls_info.position.position == 'TUNE_START':

                timestamp = hls_info.position.timestamp.timestamp()
                self.tune_time = int(timestamp * 1000)

        for marker_list in live_dict['markerLists']:
            # not including future-episodes as they are missing metadata
            if marker_list['layer'] == 'episode':
                for marker in marker_list['markers']:
                    self.episode_markers.append(XMEpisodeMarker(marker))

            elif marker_list['layer'] == 'cut':
                for marker in marker_list['markers']:
                    self.cut_markers.append(XMCutMarker(marker))

        self.cut_markers = self.sort_markers(self.cut_markers)  # type: ignore
        self.episode_markers = self.sort_markers(self.episode_markers)  # type: ignore # noqa

    @property
    def song_cuts(self) -> List[XMCutMarker]:
        """ Returns a list of all `XMCut` objects that are for songs """
        if self._song_cuts is None:
            self._song_cuts = []
            for cut in self.cut_markers:
                if isinstance(cut.cut, XMSong):
                    self._song_cuts.append(cut)
        return self._song_cuts

    @staticmethod
    def sort_markers(markers: List[XMMarker]) -> List[XMMarker]:
        """ Sorts a list of `XMMarker` objects """
        return sorted(
            markers,
            key=lambda x: x.time
        )

    def _latest_marker(self, marker_attr: str,
                       now: Optional[int] = None) -> Union[XMMarker, None]:
        """ Returns the latest `XMMarker` based on type relative to now """
        markers = getattr(self, marker_attr)
        if markers is None:
            return None

        if now is None:
            now = int(time.time() * 1000)
        latest = None
        for marker in markers:
            if now > marker.time:
                latest = marker
            else:
                break
        return latest

    def get_latest_episode(
            self, now: Optional[int] = None) -> Union[XMEpisodeMarker, None]:
        """ Returns the latest :class:`XMEpisodeMarker` based
        on type relative to now

        Parameters
        ----------
        now : Optional[:class:`int`]
            Timestamp in milliseconds from Epoch to be considered `now`
        """
        return self._latest_marker('episode_markers', now)  # type: ignore

    def get_latest_cut(
            self, now: Optional[int] = None) -> Union[XMCutMarker, None]:
        """ Returns the latest :class:`XMCutMarker` based
        on type relative to now

        Parameters
        ----------
        now : Optional[:class:`int`]
            Timestamp in milliseconds from Epoch to be considered `now`
        """
        return self._latest_marker('cut_markers', now)  # type: ignore
