#!/usr/bin/python3
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from math import floor
from Parser import MediaList
import pathlib

class Downloader:
    def __init__(self):
        self.__existing = 0
        self.__downloaded = 0
        self.__kBytes = 0

    async def load(self, media : MediaList, mediaDir : str) -> None:
        for mediaItem in media:
            track = mediaItem.getTrackNumber()
            if track >= 500:
                print(f'Skipping track {track:03d} (is audio description,...)')
                continue
            title = mediaItem.getTitle()
            url = mediaItem.getUrl()

            fileName = f'{track:03d} - {title}.mp3'
            filePath = f'{mediaDir}/{fileName}'

            if not pathlib.Path(filePath).exists():
                print(f'Loading {fileName:50s} from {url}')
                await self._download(url, filePath)
                self.__downloaded +=1
            else:
                self.__existing +=1
                print(f'{fileName} already downloaded')

    async def _download(self, url: str, fileName : str) -> None:
        try:
            f = urlopen(url)
            with open(fileName, "wb") as outFile:
                outFile.write(f.read())
            #print(f.headers)
            size = int(f.headers['content-length'])
            kb = floor(size / 1024)
            self.__kBytes += kb
            self._log(f'OK, {kb}KB')
        except HTTPError as e:
            print(f'HTTP Error: {e.code}')
        except URLError as e:
            print(f'URL Error: {e.reason}')
            
    def getLoadedCnt(self) -> int:
        return self.__downloaded
    
    def getSkippedCnt(self) -> int:
        return self.__existing
    
    def getKb(self) -> int:
        return self.__kBytes

    def _log(self, msg):
        print(msg)