#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025 allofmex
# SPDX-FileCopyrightText: 2025 techiemicky-ai
#
# SPDX-License-Identifier: MIT
#
# See the LICENSE file for more information.

import aiohttp
import random
import logging
import aiofiles
from math import floor
from Parser import MediaList
import asyncio
import pathlib
from typing import Optional, Dict

class Downloader:
    """
    Handles downloading of media files with support for parallel downloads, retries, and progress tracking.

    Features:
    - Limits the number of concurrent downloads using a semaphore.
    - Runs download tasks concurrently.
    - Tracks successfully downloaded files, skipped files, and total size.
    - Implements retry logic for failed downloads.
    - Uses a lock for thread-safe counter updates.
    - Cleans up partially downloaded files on failure.
    """
    def __init__(self):
        self.__existing = 0
        self.__downloaded = 0
        self.__kilobytes = 0
        self._lock = asyncio.Lock()

    async def load(self, session: aiohttp.ClientSession, media: MediaList, media_dir: pathlib.Path, structure: str, localeKey: Optional[str], english_titles: Optional[Dict[int, str]], force: bool, parallel_downloads: int, max_retries: int = 3, retry_delay: int = 5) -> None:
        tasks = []
        semaphore = asyncio.Semaphore(parallel_downloads)
        for mediaItem in media:
            title = mediaItem.getTitle()
            url = mediaItem.getUrl()
            track = mediaItem.getTrackNumber()

            file_title = english_titles.get(track, title) if english_titles else title

            if structure == 'flat' and localeKey:
                file_name = f'{track:03d} - {localeKey} - {file_title}.mp3' # e.g., 001 - X - English Title.mp3
            else:
                file_name = f'{track:03d} - {file_title}.mp3'

            file_path = media_dir / file_name

            if force or not file_path.exists():
                tasks.append(self._download(session, url, file_path, file_name, semaphore, max_retries, retry_delay))
            else:
                self.__existing +=1
                logging.info(f"'{file_name}' already exists, skipping.")

        if tasks:
            logging.info(f"Starting download of {len(tasks)} files with {parallel_downloads} parallel streams...")
            await asyncio.gather(*tasks)

    async def _download(self, session: aiohttp.ClientSession, url: str, file_path: pathlib.Path, file_name_log: str, semaphore: asyncio.Semaphore, max_retries: int, retry_delay: int) -> None:
        async with semaphore:
            for attempt in range(max_retries):
                try:
                    # Add a reasonable timeout for the entire request
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=300)) as response:
                        response.raise_for_status()
                        size = int(response.headers.get('content-length', 0))
                        kb = floor(size / 1024)
                        
                        # Use aiofiles for non-blocking file I/O
                        async with aiofiles.open(file_path, "wb") as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        async with self._lock:
                            self.__downloaded += 1
                            self.__kilobytes += kb
                        logging.info(f"OK: '{file_name_log}', {kb}KB")
                        return
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    logging.warning(f'Download failed for "{file_name_log}" on attempt {attempt + 1}/{max_retries}: {e}')
                    if attempt < max_retries - 1:
                        # Implement exponential backoff with jitter to make retries more robust
                        backoff_delay = retry_delay * (2 ** attempt) + random.uniform(0, 1)
                        logging.debug(f"Retrying in {backoff_delay:.2f} seconds...")
                        await asyncio.sleep(backoff_delay)
                    else:
                        logging.error(f"FAIL: Could not download '{file_name_log}' after {max_retries} attempts.")
                        # Clean up partially downloaded file
                        if file_path.exists():
                            file_path.unlink()
            
    def get_loaded_count(self) -> int:
        return self.__downloaded
    
    def get_skipped_count(self) -> int:
        return self.__existing
    
    def get_kb(self) -> int:
        return self.__kilobytes