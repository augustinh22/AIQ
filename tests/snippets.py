### https://github.com/nishad/udemy-dl/blob/master/src/udemy_dl/download.py ###
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Download files for udemy-dl."""
from __future__ import unicode_literals
from __future__ import print_function

import os
import subprocess
import sys

import colorlog
import requests

logger = colorlog.getLogger(__name__)
# User Agent String
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:39.0) Gecko/20100101 Firefox/39.0'


class DLException(Exception):

    """Raise if some lectured failed to download."""

    pass


def download(link, filename, update_progress, downloader='aria2c'):
    """Download files to given destination file-name."""
    try:
        downloader_dict = {'aria2c': aria2c_dl,
                           'axel': axel_dl,
                           'httpie': httpie_dl,
                           'curl': curl_dl,
                           'ffmpeg': ffmpeg_dl,
                           'yt_dl': youtube_dl
                           }

        external_downloader = downloader_dict.get(downloader)

        if external_downloader:
            external_downloader(link, filename)
        else:
            requests_dl(link, filename, update_progress)

    except OSError as exc:
        if not os.path.exists(filename):
            logger.critical('%s not found. Downloading with builtin downloader', downloader)
            requests_dl(link, filename, update_progress)
        else:
            logger.critical('Failed to download: %s', exc)
            download_status = 'failed'
            return download_status


def aria2c_dl(link, filename):
    """Use aria2c as the downloader."""
    command = ['aria2c', '--continue', '--file-allocation=none', '--auto-file-renaming=false', '-k', '1M', '-x', '4', '-U', USER_AGENT, link, '-o', filename]
    subprocess.call(command)
