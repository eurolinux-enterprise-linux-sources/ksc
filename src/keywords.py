# Copyright 2012 Red Hat Inc.
# Author: Kushal Das <kdas@redhat.com>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.  See
# http://www.gnu.org/copyleft/gpl.html for the full text of the
# license.
#
from pprint import pprint
import sys
import os
from utils import ksc_set
from utils import run
var = sys.version[:3]
if var in ['2.2', '2.3', '2.4']:
    set = ksc_set # pragma: no cover

keywords = set(['auto','_Bool','break','case','char','_Complex','const','continue','default',
                'do','double','else','enum','extern','float','for','goto','if','_Imaginary','inline',
                'int','long','register','restrict','return','short','signed','sizeof','static','struct',
                'switch','typedef','union','unsigned','void','volatile','while','','main'])

endpoints = set(['~','!','@','#',
                 '$','%','^','&','*',')',
                 '+','|','>','<','?','/',
                 '.',',','"',"'",':',
                 ';','-','[',']','{','}','='])


def parse_c(path, mock=False):
    """
    Parse the given C file and
    return the list of symbols
    """
    # If the file does not exists
    # then return an empty list.
    if not os.path.isfile(path):
        return []
    try:
        # We are using cpp to parse out the comments.
        data = run('cpp -fpreprocessed %s' % path)
    except:
        print "Error in opening %s" % path
        return []
    lines = data.split('\n')
    result = []
    for line in lines:
        line = line.strip()
        word = ""
        w_flag = False
        if line.startswith('#' ):
            continue

        startstr = False
        for i,c in enumerate(line):
            if c == '"':
                if not startstr:
                    startstr = True
                else:
                    if i -1 != -1:
                        if line[i-1] != '\\':
                            startstr = False
                continue
            if startstr:
                continue
            if c.isspace():
                w_flag = True
                continue
            elif c in endpoints:
                word = ""
                continue
            elif c != '(':
                if w_flag:
                    word = ""
                    w_flag = False
                    word += c
                    continue
                word += c
            elif c == '(':
                word = word.strip()
                if not word:
                    continue # pragma: no cover
                if word in keywords or word.startswith("("):
                    word = ""
                    continue
                result.append(word)
                word = ""
                w_flag = False


    #pprint(set(result))
    return set(result)
