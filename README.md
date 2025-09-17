# JW Media Downloader

A command-line tool to download media (songs, audio from magazines, etc.) from jw.org. It organizes files into a clean directory structure and uses proper titles for filenames, making it easy to manage your media library.

*Significant refactoring and the addition of unit tests were developed with the assistance of Google's Gemini Code Assist.*

## Features

- **User-Friendly Naming**: Files are saved with their proper titles (e.g., `001 - Title.mp3`) instead of cryptic filenames.
- **Organized Structure**: Media is organized by language, publication, and issue.
- **Bulk Downloads**: Download from multiple publications and for multiple languages in a single command.
- **Magazine Support**: Download audio versions of magazines like *The Watchtower* and *Awake!*.
- **Smart Downloading**: Skips files that are already downloaded to save time and bandwidth. Use `--force` to re-download everything.
- **Resilient**: Automatically retries failed downloads.
- **Flexible Structuring**: Choose between a `nested` (default) or `flat` directory structure.
- **Consistent Naming**: Option to use English names for all directories and files, regardless of the download language.
- **MP3 Player Mode**: A simple `--mp3-player` flag combines the flat structure and English naming options for perfect compatibility with simple media players.

## Setup

*This tool has been tested on Linux. It may work on other operating systems with Python 3 installed.*

1.  **Create and activate a virtual environment:**

    ```bash
    # On Debian/Ubuntu, you may need to install the venv module first
    # sudo apt install python3.11-venv
    python3 -m venv ~/jw_media_downloader_venv
    source ~/jw_media_downloader_venv/bin/activate
    ```

2.  **Install the tool:**

    Navigate to the project's root directory (where `pyproject.toml` is located).

    - **For regular use**, install the package normally:
      ```bash
      pip install .
      ```

    - **For development**, install in "editable" mode. This links the command to your source code, so any changes you make are immediately reflected without needing to reinstall.
      > **Note:** While changes to `.py` files are immediate, changes to the package metadata in `pyproject.toml` (like adding a dependency) will still require you to run this command again.

      ```bash
      pip install --editable .
      ```

## Usage

Once installed, you can run the tool from your terminal.

```bash
jw-media-downloader [OPTIONS]
```

This will download all available songs to a language specific subfolder and name them like "001 - Title.mp3".
Existing songs will be skipped, so you may run this tool periodically to add new songs.


## Examples

**1. Download Original Songs in English**

Download all "Original Songs" (`osg`) in English (`E`) to the `~/Music/JW` directory.

```bash
jw-media-downloader --target ~/Music/JW --localeKey E --pub osg
```

**2. Download a Specific Watchtower Issue in Multiple Languages**

Download the May 2025 *Watchtower* (`w:202505`) in German (`X`) and Japanese (`J`) to the `~/Downloads/JW_Media` directory, using a flat folder structure.

```bash
jw-media-downloader -t ~/Downloads/JW_Media -l X,J -p w:202505 --structure flat
```

**3. Prepare Music for a Simple MP3 Player**

Download the "Sing Out Joyfully" songbook (`sjjm`) in Tamil (`TL`) for a device that prefers flat folders and English filenames. The `--mp3-player` flag is a convenient shortcut for `--structure=flat --use-english-names`.

```bash
jw-media-downloader -t /media/my-mp3-player/music -l TL -p sjjm --mp3-player
```

**4. Download Multiple Publications at Once**

Download both the "Sing Out Joyfully" songbook (`sjjm`) and "Original Songs" (`osg`) in English.

```bash
jw-media-downloader -t ~/Music/JW -l E -p sjjm,osg
```

##### How to get the localeKey?

- Download one file in desired language manually from website
- `--localeKey` is the character(s) between '_' in the filename (German: osg_X_008.mp3 -> `x`, Japanese: osg_J_006.mp3 -> `j`)


##### Target path

The `--target` option specifies the base directory for all downloads. When using the default `nested` structure, language-specific subfolders (e.g., `en`, `fr`) will be created inside this directory.