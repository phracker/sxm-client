import time

from dataclasses import dataclass
from typing import List


REST_FORMAT = 'https://player.siriusxm.com/rest/v2/experience/modules/{}'
LIVE_PRIMARY_HLS = 'https://siriusxm-priprodlive.akamaized.net'


@dataclass
class XMArt:
    name: str = None
    url: str = None
    art_type: str = None

    def __init__(self, art_dict):
        self.name = art_dict.get('name', None)
        self.url = art_dict['url']
        self.art_type = art_dict['type']


@dataclass
class XMImage(XMArt):
    platform: str = None
    height: int = None
    width: int = None
    size: str = None

    def __init__(self, image_dict):
        image_dict['type'] = 'IMAGE'
        super().__init__(image_dict)

        self.platform = image_dict.get('platform', None)
        self.height = image_dict.get('height', None)
        self.width = image_dict.get('width', None)
        self.size = image_dict.get('size', None)


@dataclass
class XMCategory:
    guid: str = None
    name: str = None
    key: str = None
    is_primary = True

    def __init__(self, category_dict):
        self.guid = category_dict['categoryGuid']
        self.name = category_dict['name']
        self.key = category_dict['key']
        self.is_primary = category_dict['isPrimary']


@dataclass
class XMChannel:
    """See sample_data/xm_channel.json for sample"""
    guid: str = None
    id: str = None
    name: str = None
    streaming_name: str = None
    sort_order: int = None
    short_description: str = None
    medium_description: str = None
    url: str = None
    is_available: bool = True
    is_mature: bool = True
    channel_number: int = None  # actually siriusChannelNumber
    images: List[XMImage] = None
    categories: List[XMCategory] = None
    # ... plus many unused

    def __init__(self, channel_dict):
        self.guid = channel_dict['channelGuid']
        self.id = channel_dict['channelId']
        self.name = channel_dict['name']
        self.streaming_name = channel_dict['streamingName']
        self.sort_order = channel_dict['sortOrder']
        self.short_description = channel_dict['shortDescription']
        self.medium_description = channel_dict['mediumDescription']
        self.url = channel_dict['url']
        self.is_available = channel_dict['isAvailable']
        self.is_mature = channel_dict['isMature']
        self.channel_number = channel_dict['siriusChannelNumber']

        self.images = []
        for image in channel_dict['images']['images']:
            self.images.append(XMImage(image))

        self.categories = []
        for category in channel_dict['categories']['categories']:
            self.categories.append(XMCategory(category))

    @property
    def pretty_name(self):
        return f'#{self.channel_number} {self.name}'


@dataclass
class XMMarker:
    guid: str = None
    time: int = None
    duration: int = None

    def __init__(self, marker_dict):
        self.guid = marker_dict['assetGUID']
        self.time = marker_dict['time']
        self.duration = marker_dict['duration']


@dataclass
class XMShow:
    guid: str = None
    medium_title: str = None
    long_title: str = None
    short_description: str = None
    long_description: str = None
    arts: List[XMArt] = None
    # ... plus many unused

    def __init__(self, show_dict):
        self.guid = show_dict['showGUID']
        self.medium_title = show_dict['mediumTitle']
        self.long_title = show_dict['longTitle']
        self.short_description = show_dict['shortDescription']
        self.long_description = show_dict['longDescription']

        self.arts = []
        for art in show_dict['creativeArts']:
            if art['type'] == 'IMAGE':
                self.arts.append(XMImage(art))


@dataclass
class XMEpisode:
    guid: str = None
    medium_title: str = None
    long_title: str = None
    short_description: str = None
    long_description: str = None
    show: XMShow = None
    # ... plus many unused

    def __init__(self, episode_dict):
        self.guid = episode_dict['episodeGUID']
        self.medium_title = episode_dict['mediumTitle']
        self.long_title = episode_dict['longTitle']
        self.short_description = episode_dict['shortDescription']
        self.long_description = episode_dict['longDescription']
        self.show = XMShow(episode_dict['show'])


@dataclass
class XMEpisodeMarker(XMMarker):
    episode: XMEpisode = None

    def __init__(self, marker_dict):
        super().__init__(marker_dict)

        self.episode = XMEpisode(marker_dict['episode'])


@dataclass
class XMArtist:
    name: str = None

    def __init__(self, artist_dict):
        self.name = artist_dict['name']


@dataclass
class XMAlbum:
    title: str = None
    arts: List[XMArt] = None

    def __init__(self, album_dict):
        self.title = album_dict.get('title', None)

        self.arts = []
        for art in album_dict.get('creativeArts', []):
            if art['type'] == 'IMAGE':
                self.arts.append(XMImage(art))


@dataclass
class XMCut:
    title: str = None
    artists: List[XMArtist] = None
    cut_type: str = None

    def __init__(self, cut_dict):
        self.title = cut_dict['title']
        self.cut_type = cut_dict.get('cutContentType', None)

        self.artists = []
        for artist in cut_dict['artists']:
            self.artists.append(XMArtist(artist))


@dataclass
class XMSong(XMCut):
    album: XMAlbum = None
    itunes_id: str = None

    def __init__(self, song_dict):
        super().__init__(song_dict)

        if 'album' in song_dict:
            self.album = XMAlbum(song_dict['album'])

        for external_id in song_dict.get('externalIds', []):
            if external_id['id'] == 'iTunes':
                self.itunes_id = external_id['value']


@dataclass
class XMCutMarker(XMMarker):
    cut: XMCut = None

    def __init__(self, marker_dict):
        super().__init__(marker_dict)

        if marker_dict['cut'].get('cutContentType', None) == 'Song':
            self.cut = XMSong(marker_dict['cut'])
        else:
            self.cut = XMCut(marker_dict['cut'])
        # other cuts, not done: Exp, Link., maybe more?


@dataclass
class XMHLSInfo:
    name: str = None
    url: str = None
    size: str = None

    def __init__(self, hls_dict):
        self.name = hls_dict['name']
        self.url = hls_dict['url'].replace(
            '%Live_Primary_HLS%', LIVE_PRIMARY_HLS)
        self.size = hls_dict['size']


@dataclass
class XMLiveChannel:
    """See sample_data/xm_live_channel.json for sample"""

    id: str = None
    hls_infos: List[XMHLSInfo] = None
    episode_markers: List[XMEpisodeMarker] = None
    cut_markers: List[XMCutMarker] = None
    _song_cuts: List[XMCutMarker] = None
    # ... plus many unused

    def __init__(self, live_dict):
        self.id = live_dict['channelId']

        self.hls_infos = []
        self.episode_markers = []
        self.cut_markers = []

        for info in live_dict['hlsAudioInfos']:
            self.hls_infos.append(XMHLSInfo(info))

        for marker_list in live_dict['markerLists']:
            if marker_list['layer'] == 'episode':
                self.episode_markers = []
                for marker in marker_list['markers']:
                    self.episode_markers.append(XMEpisodeMarker(marker))
                self.episode_markers = self.sort_markers(self.episode_markers)

            elif marker_list['layer'] == 'cut':
                self.cut_markers = []
                for marker in marker_list['markers']:
                    self.cut_markers.append(XMCutMarker(marker))
                self.cut_markers = self.sort_markers(self.cut_markers)

    @property
    def song_cuts(self):
        if self._song_cuts is None:
            self._song_cuts = []
            for cut in self.cut_markers:
                if isinstance(cut.cut, XMSong):
                    self._song_cuts.append(cut)
        return self._song_cuts

    @staticmethod
    def sort_markers(markers):
        return sorted(
            markers,
            key=lambda x: x.time
        )

    def _latest_marker(self, marker_attr) -> XMMarker:
        markers = getattr(self, marker_attr)
        if markers is None:
            return None

        now = int(time.time() * 1000)
        latest = None
        for marker in markers:
            if now > marker.time:
                latest = marker
            else:
                break
        return latest

    def get_latest_episode(self) -> XMEpisodeMarker:
        return self._latest_marker('episode_markers')

    def get_latest_cut(self) -> XMCutMarker:
        return self._latest_marker('cut_markers')
