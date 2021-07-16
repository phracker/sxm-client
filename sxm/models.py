from __future__ import annotations

import datetime
import time
from enum import Enum
from typing import List, Optional, Tuple, Union

from pydantic import BaseModel, PrivateAttr  # pylint: disable=no-name-in-module

__all__ = [
    "XMArt",
    "XMImage",
    "XMCategory",
    "XMMarker",
    "XMShow",
    "XMEpisode",
    "XMEpisodeMarker",
    "XMArtist",
    "XMAlbum",
    "XMCut",
    "XMSong",
    "XMCutMarker",
    "XMPosition",
    "XMHLSInfo",
    "XMChannel",
    "XMLiveChannel",
    "QualitySize",
    "RegionChoice",
]


LIVE_PRIMARY_HLS = "https://siriusxm-priprodlive.akamaized.net"


class QualitySize(str, Enum):
    SMALL_64k = "SMALL"
    MEDIUM_128k = "MEDIUM"
    LARGE_256k = "LARGE"


class RegionChoice(str, Enum):
    US = "US"
    CA = "CA"


class XMArt(BaseModel):
    name: Optional[str]
    url: str
    art_type: str

    @staticmethod
    def from_dict(data: dict) -> XMArt:
        return XMArt(
            name=data.get("name", None),
            url=data["url"],
            art_type=data["type"],
        )


class XMImage(XMArt):
    platform: Optional[str] = None
    height: Optional[int] = None
    width: Optional[int] = None
    size: Optional[str] = None

    @staticmethod
    def from_dict(data: dict) -> XMImage:
        return XMImage(
            name=data.get("name", None),
            url=data["url"],
            art_type="IMAGE",
            platform=data.get("platform", None),
            height=data.get("height", None),
            width=data.get("width", None),
            size=data.get("size", None),
        )


class XMCategory(BaseModel):
    guid: str
    name: str
    key: Optional[str] = None
    order: Optional[int] = None
    short_name: Optional[str] = None

    @staticmethod
    def from_dict(data: dict) -> XMCategory:
        return XMCategory(
            guid=data["categoryGuid"],
            name=data["name"],
            key=data.get("key"),
            order=data.get("order"),
            short_name=data.get("shortName"),
        )


class XMMarker(BaseModel):
    guid: str
    time: int
    duration: int

    @staticmethod
    def from_dict(data: dict) -> XMMarker:
        return XMMarker(
            guid=data["assetGUID"],
            time=data["time"],
            duration=data["duration"],
        )


class XMShow(BaseModel):
    guid: str
    medium_title: str
    long_title: str
    short_description: str
    long_description: str
    arts: List[XMArt]
    # ... plus many unused

    @staticmethod
    def from_dict(data: dict) -> XMShow:
        arts: List[XMArt] = []
        for art in data.get("creativeArts", []):
            if art["type"] == "IMAGE":
                arts.append(XMImage.from_dict(art))

        return XMShow(
            guid=data["showGUID"],
            medium_title=data["mediumTitle"],
            long_title=data["longTitle"],
            short_description=data["shortDescription"],
            long_description=data["longDescription"],
            arts=arts,
        )


class XMEpisode(BaseModel):
    guid: str
    medium_title: str
    long_title: str
    short_description: str
    long_description: str
    show: XMShow
    # ... plus many unused

    @staticmethod
    def from_dict(data: dict) -> XMEpisode:
        return XMEpisode(
            guid=data["episodeGUID"],
            medium_title=data["mediumTitle"],
            long_title=data["longTitle"],
            short_description=data["shortDescription"],
            long_description=data["longDescription"],
            show=XMShow.from_dict(data["show"]),
        )


class XMEpisodeMarker(XMMarker):
    episode: XMEpisode

    @staticmethod
    def from_dict(data: dict) -> XMEpisodeMarker:
        return XMEpisodeMarker(
            guid=data["assetGUID"],
            time=data["time"],
            duration=data["duration"],
            episode=XMEpisode.from_dict(data["episode"]),
        )


class XMArtist(BaseModel):
    name: str

    @staticmethod
    def from_dict(data: dict) -> XMArtist:
        return XMArtist(name=data["name"])


class XMAlbum(BaseModel):
    title: Optional[str] = None
    arts: List[XMArt]

    @staticmethod
    def from_dict(data: dict) -> XMAlbum:
        arts: List[XMArt] = []
        for art in data.get("creativeArts", []):
            if art["type"] == "IMAGE":
                arts.append(XMImage.from_dict(art))

        return XMAlbum(title=data.get("title", None), arts=arts)


class XMCut(BaseModel):
    title: str
    artists: List[XMArtist]
    cut_type: Optional[str] = None

    @staticmethod
    def from_dict(data: dict) -> XMCut:
        artists: List[XMArtist] = []
        for artist in data["artists"]:
            artists.append(XMArtist.from_dict(artist))

        return XMCut(
            title=data["title"],
            cut_type=data.get("cutContentType", None),
            artists=artists,
        )


class XMSong(XMCut):
    album: Optional[XMAlbum] = None
    itunes_id: Optional[str] = None

    @staticmethod
    def from_dict(data: dict) -> XMSong:
        album: Optional[XMAlbum] = None
        itunes_id: Optional[str] = None

        if "album" in data:
            album = XMAlbum.from_dict(data["album"])

        for external_id in data.get("externalIds", []):
            if external_id["id"] == "iTunes":
                itunes_id = external_id["value"]

        artists: List[XMArtist] = []
        for artist in data["artists"]:
            artists.append(XMArtist.from_dict(artist))

        return XMSong(
            title=data["title"],
            cut_type=data.get("cutContentType", None),
            artists=artists,
            album=album,
            itunes_id=itunes_id,
        )


class XMCutMarker(XMMarker):
    cut: XMCut

    @staticmethod
    def from_dict(data: dict) -> XMCutMarker:
        if data["cut"].get("cutContentType", None) == "Song":
            cut: XMCut = XMSong.from_dict(data["cut"])
        else:
            cut = XMCut.from_dict(data["cut"])
        # other cuts, not done: Exp, Link., maybe more?

        return XMCutMarker(
            guid=data["assetGUID"],
            time=data["time"],
            duration=data["duration"],
            cut=cut,
        )


class XMPosition(BaseModel):
    timestamp: datetime.datetime
    position: str

    @staticmethod
    def from_dict(data: dict) -> XMPosition:
        dt_string = data["timestamp"].replace("+0000", "")
        dt = datetime.datetime.fromisoformat(dt_string)

        return XMPosition(
            timestamp=dt.replace(tzinfo=datetime.timezone.utc),
            position=data["position"],
        )


class XMHLSInfo(BaseModel):
    name: str
    url: str
    size: str
    position: Optional[XMPosition] = None
    # + unused chunks

    @staticmethod
    def from_dict(data: dict) -> XMHLSInfo:
        position: Optional[XMPosition] = None
        if "position" in data:
            position = XMPosition.from_dict(data["position"])

        return XMHLSInfo(
            name=data["name"],
            url=data["url"].replace("%Live_Primary_HLS%", LIVE_PRIMARY_HLS),
            size=data["size"],
            position=position,
        )


class XMChannel(BaseModel):
    """See `tests/sample_data/xm_channel.json` for sample"""

    guid: str
    id: str  # noqa A003
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

    @staticmethod
    def from_dict(data: dict):
        images: List[XMImage] = []
        for image in data["images"]["images"]:
            images.append(XMImage.from_dict(image))

        categories: List[XMCategory] = []
        for category in data["categories"]["categories"]:
            categories.append(XMCategory.from_dict(category))

        return XMChannel(
            guid=data["channelGuid"],
            id=data["channelId"],
            name=data["name"],
            streaming_name=data["streamingName"],
            sort_order=data["sortOrder"],
            short_description=data["shortDescription"],
            medium_description=data["mediumDescription"],
            url=data["url"],
            is_available=data["isAvailable"],
            is_favorite=data["isFavorite"],
            is_mature=data["isMature"],
            channel_number=data["siriusChannelNumber"],
            images=images,
            categories=categories,
        )

    @property
    def pretty_name(self) -> str:
        """Returns a formated version of channel number + channel name"""
        return f"#{self.channel_number} {self.name}"


class XMLiveChannel(BaseModel):
    """See `tests/sample_data/xm_live_channel.json` for sample"""

    id: str  # noqa A003
    hls_infos: List[XMHLSInfo]
    custom_hls_infos: List[XMHLSInfo]
    episode_markers: List[XMEpisodeMarker]
    cut_markers: List[XMCutMarker]
    tune_time: Optional[int] = None
    # ... plus many unused

    _stream_quality: QualitySize = PrivateAttr(QualitySize.LARGE_256k)
    _song_cuts: Optional[List[XMCutMarker]] = PrivateAttr(None)
    _primary_hls: Optional[XMHLSInfo] = PrivateAttr(None)
    _secondary_hls: Optional[XMHLSInfo] = PrivateAttr(None)

    @staticmethod
    def from_dict(data: dict) -> XMLiveChannel:
        hls_infos: List[XMHLSInfo] = []
        for info in data["moduleResponse"]["liveChannelData"]["hlsAudioInfos"]:
            hls_infos.append(XMHLSInfo.from_dict(info))

        custom_hls_infos = XMLiveChannel._get_custom_hls_infos(
            data["moduleResponse"]["liveChannelData"]["customAudioInfos"]
        )
        episode_markers, cut_markers = XMLiveChannel._get_markers(
            data["moduleResponse"]["liveChannelData"]["markerLists"]
        )

        return XMLiveChannel(
            id=data["channelId"],
            hls_infos=hls_infos,
            custom_hls_infos=custom_hls_infos,
            tune_time=data["wallClockRenderTime"],
            episode_markers=episode_markers,
            cut_markers=cut_markers,
        )

    def set_stream_quality(self, value: QualitySize):
        self._stream_quality = value
        self._primary_hls = None
        self._secondary_hls = None

    @property
    def primary_hls(self) -> XMHLSInfo:
        if self._primary_hls is None:
            for hls_info in self.hls_infos:
                if hls_info.name == "primary":
                    self._primary_hls = hls_info
                    # found the one we really want
                    if hls_info.size == self._stream_quality.value:
                        break

        return self._primary_hls  # type: ignore

    @property
    def secondary_hls(self) -> XMHLSInfo:
        if self._secondary_hls is None:
            for hls_info in self.hls_infos:
                if hls_info.name == "secondary":
                    self._secondary_hls = hls_info
                    # found the one we really want
                    if hls_info.size == self._stream_quality:
                        break

        return self._secondary_hls  # type: ignore

    @staticmethod
    def _get_custom_hls_infos(
        custom_infos,
    ) -> List[XMHLSInfo]:
        custom_hls_infos: List[XMHLSInfo] = []

        for info in custom_infos:
            custom_hls_infos.append(XMHLSInfo.from_dict(info))

        return custom_hls_infos

    @staticmethod
    def _get_markers(marker_lists) -> Tuple[List[XMEpisodeMarker], List[XMCutMarker]]:
        episode_markers: List[XMEpisodeMarker] = []
        cut_markers: List[XMCutMarker] = []

        for marker_list in marker_lists:
            # not including future-episodes as they are missing metadata
            if marker_list["layer"] == "episode":
                episode_markers = XMLiveChannel._get_episodes(marker_list["markers"])
            elif marker_list["layer"] == "cut":
                cut_markers = XMLiveChannel._get_cuts(marker_list["markers"])

        return episode_markers, cut_markers

    @staticmethod
    def _get_episodes(markers) -> List[XMEpisodeMarker]:
        episode_markers: List[XMEpisodeMarker] = []

        for marker in markers:
            episode_markers.append(XMEpisodeMarker.from_dict(marker))

        episode_markers = XMLiveChannel.sort_markers(episode_markers)  # type: ignore
        return episode_markers

    @staticmethod
    def _get_cuts(markers) -> List[XMCutMarker]:
        cut_markers: List[XMCutMarker] = []

        for marker in markers:
            if "cut" in marker:
                cut_markers.append(XMCutMarker.from_dict(marker))

        cut_markers = XMLiveChannel.sort_markers(cut_markers)  # type: ignore
        return cut_markers

    @property
    def song_cuts(self) -> List[XMCutMarker]:
        """Returns a list of all `XMCut` objects that are for songs"""

        if self._song_cuts is None:
            self._song_cuts = []
            for cut in self.cut_markers:
                if isinstance(cut.cut, XMSong):
                    self._song_cuts.append(cut)

        return self._song_cuts

    @staticmethod
    def sort_markers(markers: List[XMMarker]) -> List[XMMarker]:
        """Sorts a list of `XMMarker` objects"""
        return sorted(markers, key=lambda x: x.time)

    def _latest_marker(
        self, marker_attr: str, now: Optional[int] = None
    ) -> Union[XMMarker, None]:
        """Returns the latest `XMMarker` based on type relative to now"""

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
        self, now: Optional[int] = None
    ) -> Union[XMEpisodeMarker, None]:
        """Returns the latest :class:`XMEpisodeMarker` based
        on type relative to now

        Parameters
        ----------
        now : Optional[:class:`int`]
            Timestamp in milliseconds from Epoch to be considered `now`
        """
        return self._latest_marker("episode_markers", now)  # type: ignore

    def get_latest_cut(self, now: Optional[int] = None) -> Union[XMCutMarker, None]:
        """Returns the latest :class:`XMCutMarker` based
        on type relative to now

        Parameters
        ----------
        now : Optional[:class:`int`]
            Timestamp in milliseconds from Epoch to be considered `now`
        """
        return self._latest_marker("cut_markers", now)  # type: ignore
