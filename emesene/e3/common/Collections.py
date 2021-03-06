# -*- coding: utf-8 -*-

#    This file is part of emesene.
#
#    emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
#    module created by Andrea Stagi stagi.andrea(at)gmail.com
#

import os
import shutil

import logging
log = logging.getLogger('e3.common.Collections')

from Github import Github
from utils import AsyncAction

class ExtensionDescriptor(object):

    def __init__(self):
        self.files = {}

    def add_file(self, file_name, blob):
        self.files[file_name] = blob

class Collection(object):

    def __init__(self, theme, dest_folder):
        self.dest_folder = dest_folder
        self.extensions_descs = {}
        self.theme = theme
        self.github = Github("emesene")
        self._stop = False
        self._blobs = None
        self.progress = 0.0

    def save_files(self, element, label):
        self._stop = False
        if not label in element:
            return
        keys = element[label].files.keys()
        for k, path in enumerate(keys):
            self.progress = k / float(len(keys))

            split_path = path.split("/")
            if self.theme.endswith("themes"):
                removal_path = os.path.join(self.dest_folder, split_path[0], split_path[1])
            else:
                removal_path = os.path.join(self.dest_folder, split_path[0])

            if self._stop:
                self.remove(removal_path)
                return

            path_to_create = self.dest_folder
            for part in split_path[:-1]:
                path_to_create = os.path.join(path_to_create, part)
            try:
                os.makedirs(path_to_create)
            except OSError:
                pass

            try:
                rq = self.github.get_raw(self.theme, element[label].files[path])
            except Exception, ex:
                log.error(str(ex))
                self.remove(removal_path)
                return

            f = open(os.path.join(path_to_create, split_path[-1]), "wb")
            f.write(rq)
            f.close()
        self.progress = 1.0
    
    def download(self, download_item=None):
        self.progress = 0.0
        if download_item is not None:
            for element in self.extensions_descs.itervalues():
                self.save_files(element, download_item)

    def remove(self, path):
        shutil.rmtree(path)

    def stop(self):
        self._stop = True

    def set_blobs(self, result):
        self._blobs = result

    def plugin_name_from_file(self, file_name):
        pass

    def fetch(self):
        self._stop = False
        self._blobs = None
        self.progress = 0.0

        AsyncAction(self.set_blobs, self.github.fetch_blob ,self.theme)

        while self._blobs is None:
            if self._stop:
                return

        self.progress = 0.5
        j = self._blobs

        for i, k in enumerate(j["blobs"]):

            (type, name) = self.plugin_name_from_file(k)

            if type is None:
                continue

            try:
                extype = self.extensions_descs[type]
            except KeyError:
                extype = self.extensions_descs[type] = {}

            try:
                pl = extype[name]
            except KeyError:
                pl = extype[name] = ExtensionDescriptor()

            pl.add_file(k, j["blobs"][k])
            self.progress = i / float(len(j["blobs"]) * 2) + 0.5
        self.progress = 1.0

class PluginsCollection(Collection):

    def plugin_name_from_file(self, file_name):
        ps = file_name.find( "/")

        if ps != -1:
            return ("plugin", file_name[:ps])
        else:
            return (None, None)

class ThemesCollection(Collection):

    def plugin_name_from_file(self, file_name):

        ps = file_name.find( "/")
        ps = file_name.find( "/", ps + 1)

        if ps != -1:
            path = file_name[:ps]
            return path.split("/")
        else:
            return (None, None)

