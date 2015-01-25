#!/usr/bin/python

import os
import sys
import re
import string
import shutil
import errno
import urllib2
import config
import json
import imp
try:
    imp.find_module('mutagen')
    from mutagen.easyid3 import EasyID3
    from mutagen.flac import FLAC
    _music_support = True
except ImportError:
    _music_support = False

def get_config(variable, isCritical=False):
    if hasattr(config, variable):
        return getattr(config, variable)
    else:
        print "Missing config option: " + variable
        if not isCritical:
            return ""
        else:
            sys.exit(1)

class Memov:
    def __init__(self, music_support = True):
        extensions = self._createConfigList(get_config('EXTENSIONS', True))
        music_extensions = self._createConfigList(get_config('MUSIC_EXTENSIONS', True))
        movie_indicators = self._createConfigList(get_config('MOVIE_INDICATORS', True))
        ignore_files = self._createConfigList(get_config('IGNORE_FILES'))
        self.tv_pattern = re.compile("([-._ \w]+)[-._ ]S(\d{1,2}).?Ep?(\d{1,2})([^\/]*\.(?:" + extensions + ")$)", re.IGNORECASE)
        self.movie_pattern = re.compile("(?:" + movie_indicators + ")(.*)\.(?:" + extensions + ")$", re.IGNORECASE)
        self.music_pattern = re.compile("([-._ \w\(\)\[\]]+)\.(" + music_extensions + ")$", re.IGNORECASE)
        self.fileMoved = False
        self.music_support = music_support

    def isMovie(self, filename):
        result = self.movie_pattern.search(filename)
        return result

    def isTvShow(self, filename):
        result = self.tv_pattern.search(filename)
        return result

    def isMusic(self, filename):
        result = self.music_pattern.search(filename)
        return result

    def cleanUpTvShowFilename(self, matched_filename):
        matched_filename[0] = re.sub(r"[-._]", r" ", matched_filename[0].lower())
        matched_filename[0] = string.capwords(matched_filename[0])
        matched_filename.append(str(int(matched_filename[1])))
        matched_filename[1] = "%02d" % int(matched_filename[1])
        matched_filename[2] = "%02d" % int(matched_filename[2])
        matched_filename[3] = re.sub(r"^- ", r".", matched_filename[3])
        return matched_filename

    def transformTvShowFilename(self, matched_filename):
        return matched_filename[0].replace(" ", ".") + ".S" + matched_filename[1] + "E" + matched_filename[2] + matched_filename[3]

    def extractTvShowDir(self, matched_filename):
        return [matched_filename[0], matched_filename[0] + " - Season " + matched_filename[4]]

    def get_music_info(self, audio):
        artist, album = None, None
        for key in audio.keys():
            if key.lower() == 'performer' and len(audio[key]) > 0:
                artist = audio[key][0]
            elif artist == None and key.lower() == 'artist' and len(audio[key]) > 0:
                artist = audio[key][0]
            elif key.lower() == 'album' and len(audio[key]) > 0:
                album = audio[key][0]
        return artist, album

    def get_mp3_info(self, file):
        return self.get_music_info(EasyID3(file))
        
    def get_flac_info(self, file):
        return self.get_music_info(FLAC(file))

    def extractMusicDir(self, orig_file, extension):
        artist, album = None, None
        if extension.lower() == 'mp3':
            artist, album = self.get_mp3_info(orig_file)
        elif extension.lower() == 'flac':
            artist, album = self.get_flac_info(orig_file)

        if artist == None:
            return 'Unknown artist'
        elif album == None:
            return os.path.join(artist, 'Unknown album')
        else:
            return os.path.join(artist, album)

    def move(self, dir, file_name):
        orig_file = os.path.join(dir, file_name)
        tv_show_match = self.isTvShow(file_name)
        if tv_show_match:
            tv_show_title = list(tv_show_match.groups())
            tv_show_title = self.cleanUpTvShowFilename(tv_show_title)
            tv_show_dir = self.extractTvShowDir(tv_show_title)
            tv_show_title = self.transformTvShowFilename(tv_show_title)
            self.moveTvShow(orig_file, tv_show_dir, tv_show_title)
        elif self.isMovie(file_name):
            full_path = os.path.join(get_config('MOVIE_DIR', True), file_name)
            self.moveFile(orig_file, full_path)
        elif self.music_support:
            music_match = self.isMusic(file_name)
            if music_match:
                artist_album_dir = self.extractMusicDir(orig_file, music_match.groups()[1])
                full_dir = os.path.join(get_config('MUSIC_DIR', True), artist_album_dir);
                self.createDir(full_dir)
                full_path = os.path.join(full_dir, file_name)
                self.moveFile(orig_file, full_path)
            
    def moveTvShow(self, orig_file, tv_show_dir, tv_show_title):
        directory = os.path.join(get_config('TV_SHOW_DIR', True), tv_show_dir[0], tv_show_dir[1])
        self.createDir(directory)
        self.moveFile(orig_file, os.path.join(directory, tv_show_title))

    def moveFile(self, orig_file, new_file):
        print "Moving file: " + orig_file + " to " + new_file
        shutil.move(orig_file, new_file)
        self.fileMoved = True

    def createDir(self, dir):
        try:
            os.makedirs(dir)
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise

    def run(self, downloaddir):
        self.walkdir(downloaddir)
        if self.fileMoved:
            self.updateLibrary()

    def walkdir(self, dir):
        for root, subFolders, files in os.walk(dir):
            for file_name in files:
                self.move(root, file_name)
            for folder in subFolders:
                self.walkdir(folder)

    def _createConfigList(self, list_):
        result = ""
        for item in list_:
            result += item + "|"
        return result.rstrip("|")

    def updateLibrary(self):
        if get_config('XBMC_HOST') == '':
            return
        print "Updating XBMC library"
        url = 'http://' + get_config('XBMC_HOST') + "/jsonrpc"
        payload = {'jsonrpc':'2.0','method':'VideoLibrary.Scan'}
        request = urllib2.Request(url, json.dumps(payload), {'Content-Type': 'application/json'})
        stream = urllib2.urlopen(request)
        result = stream.read()
        stream.close()
        if result:
            print "Error updating library"

if __name__ == '__main__':
    download_dir = get_config('DOWNLOAD_DIR', True)
    if not _music_support:
        print 'Mutagen dependency missing. MP3/FLAC files will be skipped'

    Memov(_music_support).run(download_dir)
