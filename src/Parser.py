#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025 allofmex
# SPDX-FileCopyrightText: 2025 techiemicky-ai
#
# SPDX-License-Identifier: MIT
#
# See the LICENSE file for more information.

"""
Handles fetching and parsing media metadata from the JW.ORG API.

This module defines classes to represent media items and lists, and a Parser
class to interact with the `pub-media` API endpoint, retrieve publication
metadata, and structure it for the downloader.
"""
import aiohttp
import json
from urllib.parse import urlencode
from typing import List, Dict, Any, Optional

# Per jw.org API convention, tracks with numbers > 500 are audio descriptions.
AUDIO_DESCRIPTION_TRACK_THRESHOLD = 500

# Base URL for the JW.ORG publication media API.
JW_API_BASE_URL = 'https://b.jw-cdn.org/apis/pub-media/GETPUBMEDIALINKS'

class MediaItem:
    """Represents a single media item (e.g., a song or audio track)."""
    def __init__(self, data: Dict[str, Any]):
        self.__data = data

    def getTitle(self) -> str:
        return self.__data['title']

    def getUrl(self) -> str:
        return self.__data['file']['url']

    def getTrackNumber(self) -> int:
        return self.__data['track']

class MediaList:
    """A collection of MediaItem objects that can be iterated over."""
    def __init__(self, media_items_data: List[Dict[str, Any]]):
        self._media_data = [MediaItem(item_data) for item_data in media_items_data]
        self._index = 0
        
    def __iter__(self):
        return self
    
    def __next__(self) -> MediaItem: 
        if self._index < len(self._media_data):
            item = self._media_data[self._index]
            self._index += 1
            return item
        else:
            raise StopIteration

class Parser:
    """Fetches and parses publication metadata from the JW.ORG API."""
    def __init__(self, locale_key: str, pub: str, include_audio_descriptions: bool = False, issue: Optional[str] = None):
        self.__locale_key = locale_key
        self.__pub = pub
        self.__include_audio_descriptions = include_audio_descriptions
        self.__issue = issue
        self.__data = None
        self.__mediaList = None

    async def load(self, session: aiohttp.ClientSession) -> None:
        url = self.__createUrl()
        async with session.get(url) as response:
            response.raise_for_status()
            self.__data = await response.json()

    def printMediaList(self) -> None:
        self.__assertLoaded()
        languageStr = self.__data['languages'][self.__locale_key]['name']
        locale = self.getLocale()
        print(f'{languageStr} - {locale}')
        for mediaItem in self.getMediaList():
            title = mediaItem.getTitle()
            print(f'{title}')

    def getLocale(self) -> str:
        self.__assertLoaded()
        return self.__data['languages'][self.__locale_key]['locale']
    
    def getScript(self) -> Optional[str]:
        self.__assertLoaded()
        return self.__data['languages'][self.__locale_key].get('script')

    def getPubName(self) -> Optional[str]:
        self.__assertLoaded()
        return self.__data.get('pubName')

    def getMediaList(self) -> MediaList:
        self.__assertLoaded()
        if self.__mediaList is None:
            media_items_data = self.__data['files'][self.__locale_key]['MP3']
            
            if self.__include_audio_descriptions:
                self.__mediaList = MediaList(media_items_data)
            else:
                # Filter out audio description tracks, which have track numbers > 500.
                filtered_data = [
                    item for item in media_items_data 
                    if item.get('track', 0) <= AUDIO_DESCRIPTION_TRACK_THRESHOLD
                ]
                self.__mediaList = MediaList(filtered_data)
        return self.__mediaList

    def __createUrl(self) -> str:
        params = {
            'output': 'json',
            'pub': self.__pub,
            'fileformat': 'MP3,AAC',
            'alllangs': '0',
            'langwritten': self.__locale_key,
            'txtCMSLang': self.__locale_key
        }
        if self.__issue:
            params['issue'] = self.__issue
        args = urlencode(params)
        return f'{JW_API_BASE_URL}?{args}'

    def __assertLoaded(self) -> None:
        if self.__data is None:
            raise RuntimeError('Parser data not loaded. You must call `await parser.load()` first.')
