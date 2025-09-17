#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025 allofmex
# SPDX-FileCopyrightText: 2025 techiemicky-ai
#
# SPDX-License-Identifier: MIT
# 
# See the LICENSE file for more information.

"""
Main entry point for the JW Media Downloader command-line tool.

This script handles argument parsing, orchestrates the fetching of media metadata,
and initiates the download process for the specified languages and publications.
"""
from Downloader import Downloader
from Parser import Parser
import asyncio
import logging
import argparse
import aiohttp
import os
from importlib.metadata import version, PackageNotFoundError
from typing import List, Tuple, Optional, Dict
import pathlib

pub_map = {
    'sjjm': '"Sing Out Joyfully" to Jehovah—Meetings',
    'sjjc': '“Sing Out Joyfully” to Jehovah—Vocals',
    'sjji': '"Sing Out Joyfully" to Jehovah—Instrumental',
    'pksjj': 'Become Jehovah’s Friend—Sing With Us',
    'osg': 'Original Songs',
    'pkon': 'Become Jehovah’s Friend​—Original Songs',
    'gnjst1': 'The Good News According to Jesus—Soundtrack 1',
    'cywst': '“Commit Your Way to Jehovah”—Soundtrack',
    'snv': 'Sing to Jehovah—Chorus'
}

try:
    # Get the version from the installed package's metadata
    __version__ = version("jw_media_downloader")
except PackageNotFoundError:
    # Fallback for when the package is not installed (e.g., running from source)
    __version__ = "0.0.0-dev"

def sanitize_filename(name: str) -> str:
    """Removes characters that are invalid in file or directory names."""
    return "".join(i for i in name if i not in r'\/\\:*?"<>|')

def _parse_publications(pubs_str: str) -> List[Tuple[str, Optional[str]]]:
    """Parses the publication string into a list of (pub_code, issue) tuples."""
    parsed_pubs = []
    for item in pubs_str.split(','):
        item = item.strip()
        if ':' in item:
            pub_code, issues_str = item.split(':', 1)
            issues = [i.strip() for i in issues_str.split(';')]
            for issue in issues:
                parsed_pubs.append((pub_code, issue))
        else:
            parsed_pubs.append((item, None))
    return parsed_pubs

async def _fetch_english_info(session: aiohttp.ClientSession, parsed_pubs: List[Tuple[str, Optional[str]]]) -> Dict:
    """Fetches publication names and track titles from the English API for naming purposes."""
    logging.info("Fetching English publication info for naming...")
    english_info_map = {}
    english_locale_key = 'E'
    for pub, issue in parsed_pubs:
        try:
            # Always include audio descriptions for the English reference map to ensure it's complete.
            english_parser = Parser(english_locale_key, pub, True, issue)
            await english_parser.load(session)

            titles = {item.getTrackNumber(): item.getTitle() for item in english_parser.getMediaList()}
            english_pub_name = english_parser.getPubName() or pub_map.get(pub) or pub

            english_info_map[(pub, issue)] = {'titles': titles, 'pub_name': english_pub_name}
            logging.debug(f"OK: Fetched English info for '{pub}'" + (f" issue {issue}" if issue else ""))
        except (aiohttp.ClientError, asyncio.TimeoutError, json.JSONDecodeError) as e:
            logging.warning(f"Could not fetch English info for '{pub}'" + (f" issue {issue}" if issue else "") + f": {e}")
    return english_info_map


async def amain():
    parser = argparse.ArgumentParser(
        description="JW media downloader tool.",
        formatter_class=argparse.RawTextHelpFormatter,
        allow_abbrev=False
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}',
        help="Show the program's version number and exit."
    )
    parser.add_argument('-t', '--target', required=True, help='Target output dir to save downloaded files.')
    parser.add_argument('-l', '--localeKey', required=True, help='Comma-separated language key(s) as used on jw.org (e.g., E,X).')
    parser.add_argument(
        '-p', '--pub',
        default='osg',
        help="Comma-separated list of publications.\n"
             "For magazines, use 'pub:YYYYMM' (e.g., w:202505).\n"
             "For multiple issues, use 'pub:YYYYMM;YYYYMM' (e.g., g:202505;202506)."
    )
    parser.add_argument('--structure', choices=['nested', 'flat'], default='nested', help="Directory structure: 'nested' (hierarchical) or 'flat'.")
    parser.add_argument('--include-audio-descriptions', action='store_true', help='Include files with audio descriptions.')
    parser.add_argument('--force', action='store_true', help='Force re-download of all files, even if they exist.')
    parser.add_argument('--use-english-names', action='store_true', help='Use English names for publication directories and media files.')
    parser.add_argument('--mp3-player', action='store_true', help='Convenience flag. Equivalent to --structure=flat and --use-english-names.')
    parser.add_argument('--parallel-downloads', type=int, default=5, help='Number of parallel download streams (1 for sequential).')
    parser.add_argument('--max-retries', type=int, default=3, help='Maximum number of retries for a failed download.')
    parser.add_argument('--retry-delay', type=int, default=5, help='Delay in seconds between download retries.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging for detailed output.')

    args = parser.parse_args()

    # --- Configure Logging ---
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.info("JW media downloader tool starting...")

    # Resolve convenience flags
    structure = args.structure
    use_english_names = args.use_english_names
    if args.mp3_player:
        structure = 'flat'
        use_english_names = True

    target_path = pathlib.Path(os.path.expanduser(os.path.expandvars(args.target)))
    locale_keys = [key.strip().upper() for key in args.localeKey.split(',')]
    parsed_pubs = _parse_publications(args.pub)
    total_downloaded = 0
    total_skipped = 0
    total_kb = 0
    english_info_map = {}
    connector = aiohttp.TCPConnector(limit_per_host=args.parallel_downloads)

    async with aiohttp.ClientSession(connector=connector) as session:
        if use_english_names: # Fetch english info if needed for naming
            english_info_map = await _fetch_english_info(session, parsed_pubs)

        for locale_key in locale_keys:
            for pub, issue in parsed_pubs:
                issue_str_log = f" issue {issue}" if issue else ""
                logging.info(f"Processing pub '{pub}'{issue_str_log} for locale '{locale_key}'...")

                # Create a new Downloader for each pub to ensure summary stats are correct.
                downloader = Downloader()
                if pub in ['w', 'g'] and not issue:
                    logging.warning(f"Publication '{pub}' requires an issue (e.g., '{pub}:YYYYMM'). Skipping.")
                    continue

                try:
                    parser = Parser(locale_key, pub, args.include_audio_descriptions, issue)
                    await parser.load(session)

                    media = parser.getMediaList()
                    locale = parser.getLocale()

                    pub_dir_name = parser.getPubName() or pub_map.get(pub) or pub

                    if use_english_names:
                        english_info = english_info_map.get((pub, issue), {})
                        pub_dir_name = english_info.get('pub_name', pub_dir_name)

                    if structure == 'flat':
                        issue_str = f" - {issue}" if issue else ""
                        dir_name = f"{locale} {pub_dir_name}{issue_str}"
                        dir_name = sanitize_filename(dir_name)
                        media_dir = target_path / dir_name
                    else: # nested
                        media_dir = target_path / locale / pub_dir_name
                        if issue:
                            media_dir = media_dir / issue
                    media_dir.mkdir(parents=True, exist_ok=True)

                    english_titles = english_info_map.get((pub, issue), {}).get('titles') if use_english_names else None

                    await downloader.load(
                        session,
                        media,
                        media_dir,
                        structure,
                        locale_key,
                        english_titles,
                        args.force,
                        args.parallel_downloads,
                        args.max_retries,
                        args.retry_delay)

                    downloaded = downloader.get_loaded_count()
                    skipped = downloader.get_skipped_count()
                    kb = downloader.get_kb()
                    total_downloaded += downloaded
                    total_skipped += skipped
                    total_kb += kb
                    issue_str_fin = f"/{issue}" if issue else ""
                    logging.info(f"Finished '{pub}{issue_str_fin}/{locale_key}'. Downloaded: {downloaded}, Skipped: {skipped}, Size: {kb}KB.")
                except Exception as e:
                    logging.error(f"Could not process pub '{pub}' for locale '{locale_key}': {e}")

    logging.info(f'All done. Total downloaded: {total_downloaded}, Total skipped: {total_skipped}, Total size: {total_kb}KB.')

def main():
    """Synchronous entry point to run the asyncio main function."""
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        # This provides a cleaner exit message when the user presses Ctrl+C.
        logging.info("\nDownload cancelled by user.")

if __name__ == "__main__":
    main()