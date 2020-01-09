# Copyright 2012 Red Hat Inc.
# Author: Kushal Das <kdas@redhat.com>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.  See
# http://www.gnu.org/copyleft/gpl.html for the full text of the
# license.
#
"""This is the utility module for ksc
This contains various utility functions."""
import sys
from bugzilla import Bugzilla

import os
import base64
import getpass
import xmlrpclib

VAR = sys.version[:3]
# Try to import subprocess for latest pythons
try:  # pragma: no cover
    import subprocess
except ImportError:  # pragma: no cover
    # We don't have subprocess # pragma: no cover
    # We will use os.popen # pragma: no cover
    pass

# whitelist directory
WHPATH = '/lib/modules'
# Module.symvers directory
SRCPATH = '/usr/src/kernels'


def ksc_set(seq):
    """
    Internal implementaion set for older
    python versions
    """
    data = []
    for val in seq:
        if val not in data:
            data.append(val)
    return data


def ksc_walk(top, topdown=True, onerror=None, followlinks=False):
    """
    Internal implementation of os.walk for older
    python versions
    """
    try:
        names = os.listdir(top)
    except OSError, err:  # pragma: no cover
        print err
        return

    dirs, nondirs = [], []
    for name in names:
        if os.path.isdir(os.path.join(top, name)):
            dirs.append(name)
        else:
            nondirs.append(name)

    res = []
    res.append([top, dirs, nondirs])
    for name in dirs:
        path = os.path.join(top, name)
        if followlinks or not os.path.islink(path):  # pragma: no cover
            for fpath in ksc_walk(path, topdown, onerror, followlinks):
                res.append(fpath)
    return res


class Myfile:
    """
    Internal file like object
    """

    def __init__(self):
        self.data = ""

    def write(self, info):
        """
        Writes data
        """
        self.data = self.data + info

    def read(self):
        """
        Reads the data
        """
        return self.data


if VAR in ['2.2', '2.3', '2.4']:  # pragma: no cover
    set = ksc_set
    WALK = ksc_walk
else:
    WALK = os.walk


def get_release_name():
    if not os.path.isfile('/etc/redhat-release'):
        print 'This tool needs to run on Red Hat Enterprise Linux'
        return None

    release = open('/etc/redhat-release', 'r').read().split(' ')
    if len(release) <= 6:
        print 'This tool needs to run on Red Hat Enterprise Linux'
        return None

    return '.'.join(release[6].split('.'))


def read_list(arch, kabipath, verbose=False):
    """
    Reads a whitelist file and returns the symbols
    """
    result = []
    fpath = os.path.join(WHPATH, kabipath, "kabi_whitelist_%s" % arch)
    if not os.path.isfile(fpath):  # pragma: no cover
        print "File not found:", fpath
        return result
    try:
        if verbose:  # pragma: no cover
            print "Reading %s" % fpath
        fptr = open(fpath)
        for line in fptr.readlines():
            if line.startswith("["):
                continue
            result.append(line.strip("\n\t"))
        fptr.close()
    except IOError, err:  # pragma: no cover
        print err
        print "whitelist missing"
    return result


def read_total_list(symvers):
    """
    Reads total symbol list and returns the list
    """
    if not symvers:
        release = os.uname()[2]
        symvers = os.path.join(SRCPATH, release, "Module.symvers")
    if not os.path.isfile(symvers):  # pragma: no cover
        print "File not found:", symvers
        print "Do you have current kernel-devel package installed?"
        sys.exit(1)
    result = []
    try:
        fptr = open(symvers)
        for line in fptr.readlines():
            if line.startswith("["):
                continue  # pragma: no cover
            result.append(line.split()[1])
        fptr.close()
    except IOError, err:  # pragma: no cover
        print err
        print "Missing all symbol list"
    return result


def run(command):
    """
    runs the given command
    """
    if VAR in ['2.6', '2.7']:
        ret = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               close_fds=True)
        out, _ = ret.communicate()
    else:  # pragma: no cover
        fptr = os.popen(command)
        out = fptr.read()
    return out


def get_cfiles(path):
    """ This will return a list of C files"""
    image_list = []

    for root, _, files in WALK(path):
        for name in files:
            if name.lower().endswith('.c'):
                image_list.append(os.path.join(root, name))

    return image_list


def getconfig(path='/etc/ksc.conf', mock=False):
    """
    Returns the bugzilla config
    """
    result = {}
    result['partner'] = ''

    if not os.path.isfile(path):
        path = '/etc/ksc.conf'
    try:
        fptr = open(path)
        lines = fptr.readlines()
        fptr.close()
        for line in lines:
            if line.startswith("user="):
                result["user"] = line[5:-1]
            elif line.startswith("partner="):
                result["partner"] = line[8:-1]
            elif line.startswith("server="):
                result["server"] = line[7:-1]
            elif line.startswith("partnergroup="):
                result["group"] = line[13:-1]
        if 'user' not in result:
            print "User name is missing in configuration."
            return False
        if ('server' not in result or
                not result['server'].endswith('xmlrpc.cgi')):
            print "Servername is not valid in configuration."
            return False
        if not mock:  # pragma: no cover
            if not result['partner'] or result['partner'] == 'partner-name':
                result["partner"] = raw_input("Partner name: ")
            if not result['group'] or result['group'] == 'partner-group':
                result['group'] = raw_input("Partner group: ")
            print 'Current Bugzilla user: %s' % result['user']
            result['password'] = getpass.getpass('Please enter password: ')
        else:
            result['password'] = 'mockpassword'
        if not result['user']:
            print "Error: missing values in configuration file."
            print "Bug not submitted"
            sys.exit(1)
    except Exception, err:
        print "Error reading %s" % path
        sys.exit(1)
    return result


def createbug(filename, arch, mock=False, path='/etc/ksc.conf',
              releasename='7.0'):
    """
    Opens a bug in the Bugzilla
    """

    if releasename.startswith('6.'):
        bughash = {'product': 'Red Hat Enterprise Linux 6'}
    elif releasename.startswith('7.'):
        bughash = {'product': 'Red Hat Enterprise Linux 7'}
    else:
        print "Invalid releasename: Bug not created"
        return
    bughash["component"] = 'kernel'
    bughash["sub_component"] = 'kabi-whitelists'
    bughash["summary"] = "kABI Symbol Usage"
    bughash["version"] = releasename
    bughash["platform"] = arch
    bughash["severity"] = "medium"
    bughash["priority"] = "medium"
    bughash["description"] = "Creating the bug to attach the symbol " + \
                             "usage details."
    bughash["qa_contact"] = "kernel-qe@redhat.com"
    groups = ["redhat"]

    # We change the path if only it is mock
    if mock:
        print "Using local config file data/ksc.conf"
        path = './data/ksc.conf'

    try:
        conf = getconfig(path, mock=mock)
    except Exception, err:
        print "Problem in parsing the configuration."
        print err
        return

    if not conf:
        return
    if 'group' in conf:
        if conf['group'] != 'partner-group':
            groups.append(conf['group'])
    bughash["groups"] = groups

    bughash["Bugzilla_login"] = conf["user"]
    bughash["Bugzilla_password"] = conf["password"]
    bughash["cf_partner"] = [conf["partner"], ]

    bugid = 0
    try:
        bz = Bugzilla(
            url=conf['server'],
            user=conf["user"],
            password=conf["password"]
            )

        if not mock:  # pragma: no cover
            print "Creating a new bug"

        try:
            ret = bz.build_createbug(
                product=bughash['product'],
                component=bughash['component'],
                sub_component=bughash['sub_component'],
                summary=bughash['summary'],
                version=bughash['version'],
                platform=bughash['platform'],
                qa_contact=bughash['qa_contact'],
                severity=bughash['severity'],
                priority=bughash['priority'],
                description=bughash['description'],
                groups=bughash['groups']
                )
            ret['cf_partner'] = bughash['cf_partner']
            bug = bz.createbug(ret)

            bugid = bug.id

            if not mock:  # pragma: no cover
                print "Bug URL %s/show_bug.cgi?id=%s" % \
                    (conf['server'][:-11], bugid)
                print "Attaching the report"

            dhash = {}
            dhash["filename"] = "ksc-result.txt"
            dhash["contenttype"] = "text/plain"
            desc = "kABI symbol usage."

            fileobj = open(filename)
            attachment_id = bz.attachfile(bugid, fileobj, desc, **dhash)

            if not mock:  # pragma: no cover
                if not attachment_id:
                    print "Failed to attach symbol usage result"
                    sys.exit()
                    return
                else:
                    print "Attached successfully as %i on bug %s" % \
                        (attachment_id, bugid)

        except Exception, err:  # pragma: no cover
            print "Could not create bug. %s" % err
            if not mock:
                sys.exit(1)
    except xmlrpclib.Error, err:
        print "Bug not submitted. %s" % err
        if not mock:
            sys.exit(1)

    return bugid
