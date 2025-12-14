#!/usr/bin/python3
from Downloader import Downloader
from Parser import Parser
import sys, os, getopt, pathlib
import asyncio

def helpMsg():
    print()
    print("Tool to download collections of audio files from jw org website. (Like original songs, soundtracks,...)")
    print()
    print("Usage:")
    print("<run.sh> --target=/target/output/path --localeKey=e [--help]")
    print("t|target         Target output dir to save downloaded files")
    print("l|localeKey      Language key as used on jw org, like e for https.../lp-e/...")
    print("p|pub            Default: osg (Original Songs). Publication key as used on jw org, like osg for https...&pub=osg&...")
    print("                 (see link if you hover on headphone icon in browser")
    print()

async def main():
    targetPath = None
    localeKey = None
    pubKey = 'osg'

    print("JW media downloader tool")

    try:
        argumentList = sys.argv[1:]
        options, args = getopt.getopt(argumentList, "tlp:h", ["target=", "localeKey=", "pubKey=", "help"])
        for opt, arg in options:
            if opt in ('t', '--target'):
                targetPath = arg
            if opt in ('l', '--localeKey'):
                localeKey = arg
            if opt in ('p', '--pubKey'):
                pubKey = arg
            if opt in ('-h', '--help'):
                helpMsg()
                sys.exit()
    except getopt.GetoptError as e:
        print(e)
        helpMsg()
        sys.exit(2)

    if targetPath is None:
        print('Failure: No target path specified, provide --target parameter')
        helpMsg()
        sys.exit(3)
    if localeKey is None:
        print('Failure: No locale key specified, provide --localeKey parameter')
        helpMsg()
        sys.exit(4)

    targetPath = os.path.expanduser(os.path.expandvars(targetPath))
    localeKey = localeKey.upper()
    print(f'Searching for locale {localeKey} and publication {pubKey}')
    print(f'Target path is {targetPath}')
    parser = Parser(localeKey)
    parser.load(pubKey)
    #parser.printMediaList()

    media = parser.getMediaList()
    locale = parser.getLocale()
    mediaDir = os.path.join(targetPath, locale)
    path = pathlib.Path(mediaDir)
    if not path.exists():
        print('Creating dir '+mediaDir)
        path.mkdir(parents=True, exist_ok=True)

    downloader = Downloader();
    await downloader.load(media, mediaDir)
    print(f'Done. Downloaded: {downloader.getLoadedCnt()}, skipped: {downloader.getSkippedCnt()}, total: {downloader.getKb()}KB.')

if __name__ == "__main__":
    asyncio.run(main())