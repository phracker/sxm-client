import datetime
from pydantic import BaseModel
from typing import List, Optional, Union

class XMArt(BaseModel):
    name: Optional[str]
    url: str
    art_type: str
    @staticmethod
    def from_dict(data: dict) -> XMArt: ...

class XMImage(XMArt):
    platform: Optional[str]
    height: Optional[int]
    width: Optional[int]
    size: Optional[str]
    @staticmethod
    def from_dict(data: dict) -> XMImage: ...

class XMCategory(BaseModel):
    guid: str
    name: str
    key: Optional[str]
    order: Optional[int]
    short_name: Optional[str]
    @staticmethod
    def from_dict(data: dict) -> XMCategory: ...

class XMMarker(BaseModel):
    guid: str
    time: int
    duration: int
    @staticmethod
    def from_dict(data: dict) -> XMMarker: ...

class XMShow(BaseModel):
    guid: str
    medium_title: str
    long_title: str
    short_description: str
    long_description: str
    arts: List[XMArt]
    @staticmethod
    def from_dict(data: dict) -> XMShow: ...

class XMEpisode(BaseModel):
    guid: str
    medium_title: str
    long_title: str
    short_description: str
    long_description: str
    show: XMShow
    @staticmethod
    def from_dict(data: dict) -> XMEpisode: ...

class XMEpisodeMarker(XMMarker):
    episode: XMEpisode
    @staticmethod
    def from_dict(data: dict) -> XMEpisodeMarker: ...

class XMArtist(BaseModel):
    name: str
    @staticmethod
    def from_dict(data: dict) -> XMArtist: ...

class XMAlbum(BaseModel):
    title: Optional[str]
    arts: List[XMArt]
    @staticmethod
    def from_dict(data: dict) -> XMAlbum: ...

class XMCut(BaseModel):
    title: str
    artists: List[XMArtist]
    cut_type: Optional[str]
    @staticmethod
    def from_dict(data: dict) -> XMCut: ...

class XMSong(XMCut):
    album: Optional[XMAlbum]
    itunes_id: Optional[str]
    @staticmethod
    def from_dict(data: dict) -> XMSong: ...

class XMCutMarker(XMMarker):
    cut: XMCut
    @staticmethod
    def from_dict(data: dict) -> XMCutMarker: ...

class XMPosition(BaseModel):
    timestamp: datetime.datetime
    position: str
    @staticmethod
    def from_dict(data: dict) -> XMPosition: ...

class XMHLSInfo(BaseModel):
    name: str
    url: str
    size: str
    position: Optional[XMPosition]
    @staticmethod
    def from_dict(data: dict) -> XMHLSInfo: ...

class XMChannel(BaseModel):
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
    channel_number: int
    images: List[XMImage]
    categories: List[XMCategory]
    @staticmethod
    def from_dict(data: dict): ...
    @property
    def pretty_name(self) -> str: ...

class XMLiveChannel(BaseModel):
    id: str
    hls_infos: List[XMHLSInfo]
    custom_hls_infos: List[XMHLSInfo]
    episode_markers: List[XMEpisodeMarker]
    cut_markers: List[XMCutMarker]
    tune_time: Optional[int]
    @staticmethod
    def from_dict(data: dict) -> XMLiveChannel: ...
    @property
    def song_cuts(self) -> List[XMCutMarker]: ...
    @staticmethod
    def sort_markers(markers: List[XMMarker]) -> List[XMMarker]: ...
    def get_latest_episode(self, now: Optional[int] = ...) -> Union[XMEpisodeMarker, None]: ...
    def get_latest_cut(self, now: Optional[int] = ...) -> Union[XMCutMarker, None]: ...
