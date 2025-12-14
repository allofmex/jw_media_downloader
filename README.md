# Media Download Tool

This tool can download media items from jw org website to be saved locally.
It will use the real title as file name (not like the filename code if you download
them manually via website)

**Original Songs (mp3) implemented only - as of now**

## Setup

Tested on Unix only, may work also on Windows.

Create virtual environment

```
apt install python3.12-venv
python3 -m venv ~/jw_media_tool_venv
```

Activate virtual environment

```
source ~/jw_media_tool_venv/bin/activate

pip3 install .
# pip3 install --editable .
```


## Usage

```
source ~/jw_media_tool_venv/bin/activate
./run.sh --target=~/output/path --localeKey=e
```

This will download all available songs to a language specific subfolder and name them like "001 - Title.mp3".
Existing songs will be skipped, so you may run this tool periodically to add new songs.


##### How to get the localeKey?

- Download one file in desired language manually from website
- `--localeKey` is the character(s) between '_' in the filename (German: osg_X_008.mp3 -> `x`, Japanese: osg_J_006.mp3 -> `j`)


##### Target path

`--target` option is for all locales. This tool will create subfolder by language (en, fr,..)