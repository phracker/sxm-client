import base64
import datetime
import json
import logging
import time
import urllib.parse

import requests

from fake_useragent import UserAgent

from .models import LIVE_PRIMARY_HLS, REST_FORMAT, XMLiveChannel

__all__ = ['HLS_AES_KEY', 'SiriusXMClient']


HLS_AES_KEY = base64.b64decode('0Nsco7MAgxowGvkUT8aYag==')
FALLBACK_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'  # noqa


class SiriusXMClient:
    def __init__(self, username, password,
                 user_agent=None, update_handler=None):
        self._log = logging.getLogger(__file__)

        if user_agent is not None:
            self._ua = user_agent
        else:
            try:
                self._ua = UserAgent().data_browsers['chrome'][0]
            except Exception:
                self._ua = FALLBACK_UA

        self.session = requests.Session()
        self.session.headers.update(
            {'User-Agent': self._ua})

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
            postdata = {
                'moduleList': {
                    'modules': [{
                        'moduleArea': 'Discovery',
                        'moduleType': 'ChannelListing',
                        'moduleRequest': {
                            'consumeRequests': [],
                            'resultTemplate': 'responsive',
                            'alerts': [],
                            'profileInfos': []
                        }
                    }]
                }
            }
            data = self._post('get', postdata)
            if not data:
                self._log.warn('Unable to get channel list')
                return (None, None)

            try:
                self._channels = data['moduleList']['modules'][0]['moduleResponse']['contentData']['channelListing']['channels']
            except (KeyError, IndexError):
                self._log.error('Error parsing json response for channels')
                return []
            else:
                self._channels = sorted(
                    self._channels,
                    key=lambda x: int(x.get('siriusChannelNumber', 9999))
                )
        return self._channels

    @property
    def favorite_channels(self):
        if self._favorite_channels is None:
            self._favorite_channels = [
                c for c in self.channels if c.get('isFavorite', False)
            ]
        return self._favorite_channels

    def login(self):
        postdata = {
            'moduleList': {
                'modules': [{
                    'moduleRequest': {
                        'resultTemplate': 'web',
                        'deviceInfo': {
                            'osVersion': 'Mac',
                            'platform': 'Web',
                            'sxmAppVersion': '3.1802.10011.0',
                            'browser': 'Safari',
                            'browserVersion': '11.0.3',
                            'appRegion': 'US',
                            'deviceModel': 'K2WebClient',
                            'clientDeviceId': 'null',
                            'player': 'html5',
                            'clientDeviceType': 'web',
                        },
                        'standardAuth': {
                            'username': self.username,
                            'password': self.password,
                        },
                    },
                }],
            },
        }
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

    def authenticate(self):
        if not self.is_logged_in and not self.login():
            self._log.error('Unable to authenticate because login failed')
            return False

        postdata = {
            'moduleList': {
                'modules': [{
                    'moduleRequest': {
                        'resultTemplate': 'web',
                        'deviceInfo': {
                            'osVersion': 'Mac',
                            'platform': 'Web',
                            'clientDeviceType': 'web',
                            'sxmAppVersion': '3.1802.10011.0',
                            'browser': 'Safari',
                            'browserVersion': '11.0.3',
                            'appRegion': 'US',
                            'deviceModel': 'K2WebClient',
                            'player': 'html5',
                            'clientDeviceId': 'null'
                        }
                    }
                }]
            }
        }
        data = self._post('resume?OAtrial=false', postdata, authenticate=False)
        if not data:
            return False

        try:
            return data['status'] == 1 \
                and self.is_session_authenticated
        except KeyError:
            self._log.error('Error parsing json response for authentication')
            return False

    def get_playlist(self, name, use_cache=True):
        channel = self.get_channel(name)
        guid, channel_id = channel['channelGuid'], channel['channelId']

        if not guid or not channel_id:
            self._log.info(f'No channel for {name}')
            return None

        url = self._get_playlist_url(guid, channel_id, use_cache)
        if url is None:
            return None

        params = {
            'token': self.sxmak_token,
            'consumer': 'k2',
            'gupId': self.gup_id,
        }
        res = self.session.get(url, params=params)

        if res.status_code == 403:
            self._log.info(
                'Received status code 403 on playlist, renewing session')
            return self.get_playlist(name, False)

        if res.status_code != 200:
            self._log.warn(
                f'Received status code {res.status_code} on playlist variant')
            return None

        # add base path to segments
        base_url = url.rsplit('/', 1)[0]
        base_path = base_url[8:].split('/', 1)[1]
        lines = res.text.split('\n')
        for x in range(len(lines)):
            if lines[x].rstrip().endswith('.aac'):
                lines[x] = f'{base_path}/{lines[x]}'
        return '\n'.join(lines)

    def get_segment(self, path, max_attempts=5):
        url = f'{LIVE_PRIMARY_HLS}/{path}'
        params = {
            'token': self.sxmak_token,
            'consumer': 'k2',
            'gupId': self.gup_id,
        }
        res = self.session.get(url, params=params)

        if res.status_code == 403:
            if max_attempts > 0:
                self._log.info(
                    'Received status code 403 on segment, renewing session')
                self.get_playlist(path.split('/', 2)[1], False)
                return self.get_segment(path, max_attempts - 1)
            else:
                self._log.warn(
                    'Received status code 403 on segment, '
                    'max attempts exceeded'
                )
                return None

        if res.status_code != 200:
            self._log.warn(
                f'Received status code {res.status_code} on segment')
            return None

        return res.content

    def get_channel(self, name):
        name = name.lower()
        for x in self.channels:
            if x.get('name', '').lower() == name or \
                    x.get('channelId', '').lower() == name or \
                    x.get('siriusChannelNumber') == name:
                return x
        return None

    def _get(self, method, params, authenticate=True):
        if authenticate and not self.is_session_authenticated and \
                not self.authenticate():
            self._log.error('Unable to authenticate')
            return None

        res = self.session.get(REST_FORMAT.format(method), params=params)
        if res.status_code != 200:
            self._log.warn(
                f'Received status code {res.status_code} '
                f'for method \'{method}\''
            )
            return None

        try:
            return res.json()['ModuleListResponse']
        except (KeyError, ValueError):
            self._log.error(f'Error decoding json for method \'{method}\'')
            return None

    def _post(self, method, postdata, authenticate=True):
        if authenticate and not self.is_session_authenticated and \
                not self.authenticate():
            self._log.error('Unable to authenticate')
            return None

        res = self.session.post(
            REST_FORMAT.format(method),
            data=json.dumps(postdata)
        )
        if res.status_code != 200:
            self._log.warn(
                f'Received status code {res.status_code} for '
                f'method \'{method}\''
            )
            return None

        try:
            return res.json()['ModuleListResponse']
        except (KeyError, ValueError):
            self._log.error(f'Error decoding json for method \'{method}\'')
            return None

    def _get_playlist_url(self, guid, channel_id,
                          use_cache=True, max_attempts=5):
        now = time.time()

        if use_cache and channel_id in self.playlists:
            if self.last_renew is None or \
                    (now - self.last_renew) > self.update_interval:
                del self.playlists[channel_id]
            else:
                return self.playlists[channel_id]

        params = {
            'assetGUID': guid,
            'ccRequestType': 'AUDIO_VIDEO',
            'channelId': channel_id,
            'hls_output_mode': 'custom',
            'marker_mode': 'all_separate_cue_points',
            'result-template': 'web',
            'time': int(round(time.time() * 1000.0)),
            'timestamp': datetime.datetime.utcnow().isoformat('T') + 'Z'
        }
        data = self._get('tune/now-playing-live', params)
        if not data:
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
                        guid, channel_id, use_cache, max_attempts - 1)
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
                    self.playlists[channel_id] = playlist
                    self.last_renew = time.time()

                    if self.update_handler is not None:
                        self.update_handler(live_channel_raw)
                    return self.playlists[channel_id]
        return None

    def _get_playlist_variant_url(self, url):
        params = {
            'token': self.sxmak_token,
            'consumer': 'k2',
            'gupId': self.gup_id,
        }
        res = self.session.get(url, params=params)

        if res.status_code != 200:
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
