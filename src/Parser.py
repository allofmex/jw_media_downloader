#!/usr/bin/python3
#from HTMLParser import HTMLParser
from urllib.request import urlopen
import json

class MediaItem:
    def __init__(self, data):
        self.__data = data

    def getTitle(self) -> str:
        return self.__data['title']

    def getUrl(self) -> str:
        return self.__data['file']['url']

    def getTrackNumber(self) -> int:
        return self.__data['track']
 
class MediaList:
    def __init__(self, mediaItem):
        self._mediaData = []
        for mediaItemData in mediaItem:
            self._mediaData.append(MediaItem(mediaItemData))
        self._index = 0
        
    def __iter__(self):
        return self
    
    def __next__(self) -> MediaItem: 
        if self._index < len(self._mediaData):
            item = self._mediaData[self._index]
            self._index += 1
            return item
        else:
            raise StopIteration

class Parser:
    def __init__(self, localeKey : str):
        self.__localeKey = localeKey
        self.__data = None
        self.__mediaList = None

    def load(self) -> None:
        url = self.__createUrl()
        with urlopen(url) as response:
            html_page = response.read()
            self.__data = json.loads(html_page)

    def printMediaList(self) -> None:
        self.__assertLoaded()
        languageStr = self.__data['languages'][self.__localeKey]['name']
        locale = self.getLocale()
        print(f'{languageStr} - {locale}')
        for mediaItem in self.getMediaList():
            title = mediaItem.getTitle()
            print(f'{title}')

    def getLocale(self) -> str:
        self.__assertLoaded()
        return self.__data['languages'][self.__localeKey]['locale']
    
    def getMediaList(self) -> MediaList:
        self.__assertLoaded()
        if self.__mediaList is None:
            self.__mediaList = MediaList(self.__data['files'][self.__localeKey]['MP3'])
        return self.__mediaList

    def __createUrl(self) -> str:
        args = f'output=json&pub=osg&fileformat=MP3%2CAAC&alllangs=0&langwritten={self.__localeKey}&txtCMSLang={self.__localeKey}'
        return f'https://b.jw-cdn.org/apis/pub-media/GETPUBMEDIALINKS?{args}'

    def __assertLoaded(self) -> None:
        if self.__data is None:
            raise Exception('No __data present! You must call load() first')
