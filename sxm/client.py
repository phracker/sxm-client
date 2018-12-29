import base64
import datetime
import json
import logging
import re
import time
import urllib.parse

import requests

from fake_useragent import FakeUserAgent
from tenacity import retry, stop_after_attempt, wait_fixed
from ua_parser import user_agent_parser

from .models import LIVE_PRIMARY_HLS, REST_FORMAT, XMChannel, XMLiveChannel

__all__ = ['HLS_AES_KEY', 'SiriusXMClient']


SXM_APP_VERSION = '5.15.2183'
SXM_DEVICE_MODEL = 'EverestWebClient'
HLS_AES_KEY = base64.b64decode('0Nsco7MAgxowGvkUT8aYag==')
FALLBACK_UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/604.5.6 (KHTML, like Gecko) Version/11.0.3 Safari/604.5.6'  # noqa


class AuthenticationError(Exception):
    pass


class SegmentRetrievalException(Exception):
    pass


class SiriusXMClient:
    def __init__(self, username, password,
                 user_agent=None, update_handler=None):
        self._log = logging.getLogger(__file__)

        if user_agent is not None:
            self._ua = user_agent
        else:
            try:
                self._ua = FakeUserAgent().data_browsers['chrome'][0]
            except Exception:
                self._ua = FALLBACK_UA
        self._ua = user_agent_parser.Parse(self._ua)

        self._reset_session()

        self.username = username
        self.password = password

        self.playlists = {}
        self._channels = None
        self._favorite_channels = None

        # vars to manage session cache
        self.last_renew = None
        self.update_interval = 30

        # hook function to call whenever the playlist updates
        self.update_handler = update_handler

    @property
    def is_logged_in(self):
        return 'SXMAUTH' in self.session.cookies

    @property
    def is_session_authenticated(self):
        return 'AWSELB' in self.session.cookies and \
            'JSESSIONID' in self.session.cookies

    @property
    def sxmak_token(self):
        try:
            token = self.session.cookies['SXMAKTOKEN']
            return token.split('=', 1)[1].split(',', 1)[0]
        except (KeyError, IndexError):
            return None

    @property
    def gup_id(self):
        try:
            data = self.session.cookies['SXMDATA']
            return json.loads(urllib.parse.unquote(data))['gupId']
        except (KeyError, ValueError):
            return None

    @property
    def channels(self):
        # download channel list if necessary
        if self._channels is None:
            channels = self.get_channels()

            if len(channels) > 0:
                self._channels = channels
                self._channels = sorted(
                    self._channels,
                    key=lambda x: int(x.channel_number)
                )
            else:
                return channels
        return self._channels

    @property
    def favorite_channels(self):
        if self._favorite_channels is None:
            self._favorite_channels = [
                c for c in self.channels if c.is_favorite
            ]
        return self._favorite_channels

    def login(self):
        postdata = self._get_device_info()
        postdata.update({
            'standardAuth': {
                'username': self.username,
                'password': self.password,
            },
        })

        data = self._post(
            'modify/authentication', postdata,
            authenticate=False
        )
        if not data:
            return False

        try:
            return data['status'] == 1 \
                and self.is_logged_in
        except KeyError:
            self._log.error('Error decoding json response for login')
            return False

    @retry(wait=wait_fixed(3), stop=stop_after_attempt(10))
    def authenticate(self):
        if not self.is_logged_in and not self.login():
            self._log.error('Unable to authenticate because login failed')
            self._reset_session()
            raise AuthenticationError('Reset session')

        data = self._post(
            'resume?OAtrial=false',
            self._get_device_info(),
            authenticate=False
        )
        if not data:
            return False

        try:
            return data['status'] == 1 \
                and self.is_session_authenticated
        except KeyError:
            self._log.error('Error parsing json response for authentication')
            return False

    @retry(stop=stop_after_attempt(25), wait=wait_fixed(1))
    def get_playlist(self, name, use_cache=True):
        channel = self.get_channel(name)

        if channel is None:
            self._log.info(f'No channel for {name}')
            return None

        url = self._get_playlist_url(channel, use_cache)
        if url is None:
            return None

        try:
            res = self.session.get(url, params=self._token_params())

            if res.status_code == 403:
                self._log.info(
                    'Received status code 403 on playlist, renewing session')
                return self.get_playlist(name, False)

            if not res.ok:
                self._log.warn(
                    f'Received status code {res.status_code} on '
                    f'playlist variant'
                )
                return None

        except requests.exceptions.ConnectionError as e:
            self._log.error(f'Error getting playlist: {e}')
            return None

        # add base path to segments
        playlist_entries = []
        aac_path = re.findall("AAC_Data.*", url)[0]
        for line in res.text.split("\n"):
            line = line.strip()
            if line.endswith(".aac"):
                playlist_entries.append(
                    re.sub("[^\/]\w+\.m3u8", line, aac_path)
                )
            else:
                playlist_entries.append(line)

        return "\n".join(playlist_entries)

    @retry(wait=wait_fixed(1), stop=stop_after_attempt(5))
    def get_segment(self, path, max_attempts=5):
        url = f'{LIVE_PRIMARY_HLS}/{path}'
        res = self.session.get(url, params=self._token_params())

        if res.status_code == 403:
            raise SegmentRetrievalException(
                "Received status code 403 on segment, renewed session"
            )

        if not res.ok:
            self._log.warn(
                f'Received status code {res.status_code} on segment')
            return None

        return res.content

    def get_channels(self):
        channels = []

        postdata = {
            'consumeRequests': [],
            'resultTemplate': 'responsive',
            'alerts': [],
            'profileInfos': []
        }

        data = self._post('get', postdata, channel_list=True)
        if not data:
            self._log.warn('Unable to get channel list')
            return channels

        try:
            channels = data['moduleList']['modules'][0]['moduleResponse']['contentData']['channelListing']
        except (KeyError, IndexError):
            self._log.error('Error parsing json response for channels')
            return []
        return channels

    def get_channel(self, name):
        name = name.lower()
        for x in self.channels:
            if x.name.lower() == name or \
                    x.id.lower() == name or \
                    x.channel_number == name:
                return x
        return None

    def _reset_session(self):
        self.session = requests.Session()
        self.session.headers.update(
            {'User-Agent': self._ua['string']})

    def _token_params(self):
        return {
            "token": self.sxmak_token,
            "consumer": "k2",
            "gupId": self.gup_id,
        }

    def _get_device_info(self):
        browser_version = self._ua['user_agent']['major']
        if self._ua['user_agent']['minor'] is not None:
            browser_version = \
                f'{browser_version}.{self._ua["user_agent"]["minor"]}'
        if self._ua['user_agent']['patch'] is not None:
            browser_version = \
                f'{browser_version}.{self._ua["user_agent"]["patch"]}'

        return {
            "resultTemplate": "web",
            "deviceInfo": {
                "osVersion": "Mac",
                "platform": "Web",
                "sxmAppVersion": "3.1802.10011.0",
                "browser": "Safari",
                "browserVersion": "11.0.3",
                "appRegion": "US",
                "deviceModel": "K2WebClient",
                "clientDeviceId": "null",
                "player": "html5",
                "clientDeviceType": "web",
            }
        }

        return {
            'resultTemplate': 'web',
            'deviceInfo': {
                'osVersion': self._ua['os']['family'],
                'platform': 'Web',
                'sxmAppVersion': SXM_APP_VERSION,
                'browser': self._ua['user_agent']['family'],
                'browserVersion': browser_version,
                'appRegion': 'US',
                'deviceModel': SXM_DEVICE_MODEL,
                'clientDeviceId': 'null',
                'player': 'html5',
                'clientDeviceType': 'web',
            }
        }

    def _request(self, method, path, params, authenticate=True):
        method = method.upper()

        if authenticate and \
                not self.is_session_authenticated and \
                not self.authenticate():

            self._log.error('Unable to authenticate')
            return None

        try:
            url = REST_FORMAT.format(path)

            if method == 'GET':
                res = self.session.get(url, params=params)
            elif method == 'POST':
                res = self.session.post(url, data=json.dumps(params))
            else:
                raise requests.RequestException('only GET and POST')
        except requests.exceptions.ConnectionError as e:
            self._log.error(
                f'An Exception occurred when trying to perform '
                f'the {method} request!'
            )
            self._log.error(f'Params: {params}')
            self._log.error(f'Method: {method}')
            self._log.error(f'Response: {e.response}')
            self._log.error(f'Request: {e.request}')
            raise (e)

        if not res.ok:
            self._log.warn(
                f'Received status code {res.status_code} for path \'{path}\'')
            return None

        try:
            return res.json()['ModuleListResponse']
        except (KeyError, ValueError):
            self._log.error(f'Error decoding json for path \'{path}\'')
            return None

    def _get(self, path, params, authenticate=True):
        return self._request('GET', path, params, authenticate)

    def _post(self, path, postdata, channel_list=False, authenticate=True):
        postdata = {
            'moduleList': {
                'modules': [{
                    'moduleRequest': postdata,
                }],
            },
        }

        if channel_list:
            postdata['moduleList']['modules'][0].update({
                'moduleArea': 'Discovery',
                'moduleType': 'ChannelListing'
            })

        return self._request('POST', path, postdata, authenticate)

    def get_now_playing(self, channel):
        params = {
            "assetGUID": channel.guid,
            "ccRequestType": "AUDIO_VIDEO",
            "channelId": channel.id,
            "hls_output_mode": "custom",
            "marker_mode": "all_separate_cue_points",
            "result-template": "web",
            "time": int(round(time.time() * 1000.0)),
            "timestamp": datetime.datetime.utcnow().isoformat("T") + "Z",
        }

        return self._get("tune/now-playing-live", params)

    def _get_playlist_url(self, channel, use_cache=True, max_attempts=5):
        now = time.time()

        if use_cache and channel.id in self.playlists:
            if self.last_renew is None or \
                    (now - self.last_renew) > self.update_interval:

                del self.playlists[channel.id]
            else:
                return self.playlists[channel.id]

        data = self.get_now_playing(channel)
        if data is None:
            return None

        # parse response
        try:
            self.update_interval = int(
                data['moduleList']['modules'][0]['updateFrequency']
            )

            message = data['messages'][0]['message']
            message_code = data['messages'][0]['code']

            live_channel_raw = data['moduleList']['modules'][0]['moduleResponse']['liveChannelData']  # noqa
            live_channel = XMLiveChannel(live_channel_raw)

        except (KeyError, IndexError):
            self._log.error('Error parsing json response for playlist')
            return None

        # login if session expired
        if message_code == 201 or message_code == 208:
            if max_attempts > 0:
                self._log.info(
                    'Session expired, logging in and authenticating')
                if self.authenticate():
                    self._log.info('Successfully authenticated')
                    return self._get_playlist_url(
                        channel, use_cache, max_attempts - 1)
                else:
                    self._log.error('Failed to authenticate')
                    return None
            else:
                self._log.warn('Reached max attempts for playlist')
                return None
        elif message_code != 100:
            self._log.warn(f'Received error {message_code} {message}')
            return None

        # get m3u8 url
        for playlist_info in live_channel.hls_infos:
            if playlist_info.size == 'LARGE':
                playlist = self._get_playlist_variant_url(playlist_info.url)

                if playlist is not None:
                    self.playlists[channel.id] = playlist
                    self.last_renew = time.time()

                    if self.update_handler is not None:
                        self.update_handler(live_channel_raw)
                    return self.playlists[channel.id]
        return None

    def _get_playlist_variant_url(self, url):
        res = self.session.get(url, params=self._token_params())

        if not res.ok:
            self._log.warn(
                f'Received status code {res.status_code} on playlist '
                f'variant retrieval'
            )
            return None

        for x in res.text.split('\n'):
            if x.rstrip().endswith('.m3u8'):
                # first variant should be 256k one
                return '{}/{}'.format(url.rsplit('/', 1)[0], x.rstrip())

        return None
