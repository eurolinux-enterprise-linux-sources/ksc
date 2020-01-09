#!/usr/bin/env python
# Copyright 2012 Red Hat Inc.
# Author: Kushal Das <kdas@redhat.com>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.  See
# http://www.gnu.org/copyleft/gpl.html for the full text of the
# license.
#
import os
import sys
import tempfile
from pprint import pprint
from optparse import OptionParser
from utils import run, read_list
from utils import read_total_list, get_cfiles, get_release_name
from utils import encode_base64
from utils import createbug
from utils import ksc_set
from keywords import endpoints, keywords, parse_c

KSCVERSION = "ksc - Version 0.9.14"

var = sys.version[:3]
if var in ['2.2', '2.3', '2.4']:# pragma: no cover
    set = ksc_set

class Ksc(object):
    def __init__ (self, mock = False):
        """
        Init call
        """
        self.all_symbols_used = []
        self.nonwhite_symbols_used = []
        self.white_symbols = []
        self.matchdata = None
        self.total = None
        self.tmplist = []
        self.verbose = False
        self.mock = mock
        self.releasedir = None
        self.arch = None
        if mock:
            self.releasename = '7.0'
        else:
            self.releasename = None
        self.release_choices = ['6.0', '6.1', '6.2', '6.3', '6.4', '6.5', '6.6', '7.0']


    def clean(self):
        self.all_symbols_used = []
        self.nonwhite_symbols_used = []
        self.white_symbols = []
        self.matchdata = None
        self.total = None


    def main(self, mock_options=None):
        """
        Main function for the logic
        """
        filename = os.path.join(os.path.expanduser("~"),"ksc-result.txt")
        #default architecture
        self.arch = "x86_64"

        parser = OptionParser()
        parser.add_option("-c", "--config", dest="config",
                          help="path to configuration file", metavar="CONFIG")
        parser.add_option("-d", "--directory", dest="directory",
                          help="path to the directory", metavar="DIRECTORY")
        parser.add_option("-i", "--internal", action="store_true", dest="internal",
                          help="to create text files to be used internally ", metavar="INTERNAL")
        parser.add_option("-k", "--ko", dest="ko",
                          help="path to the ko file", metavar="KO")
        parser.add_option("-n", "--name", dest="releasename",
                          help="Red Hat release to file the bug against", metavar="RELEASENAME")
        parser.add_option("-p", "--previous", dest="previous",
                          help="path to previous resultset to submit as bug")
        parser.add_option("-r", "--release", dest="release",
                          help="RHEL whitelist release to compare against", metavar="RELEASE")
        parser.add_option("-s", "--submit",
                  action="store_true", dest="submit", default=False,
                  help="Submit to Red Hat Bugzilla")
        parser.add_option("-v", "--version",
                  action="store_true", dest="VERSION", default=False,
                  help="Prints KSC version number")



        if not self.mock: # pragma: no cover
            (options, args) = parser.parse_args(sys.argv[1:])
        else: # pragma: no cover
            (options, args) = parser.parse_args(mock_options)

        if options.VERSION:
            print KSCVERSION
            sys.exit(0)

        #Create the ksc.conf config path
        if options.config:
            path = os.path.abspath(os.path.expanduser(options.config))
        else:
            path = os.path.join(os.path.expanduser("~"),"ksc.conf")


        if options.releasename:
            self.releasename = options.releasename
            if self.releasename not in self.release_choices:
                print "Invalid RHEL release name with -n option."
                return

        if options.previous: #Submit the result of previous run
            filename = os.path.abspath(os.path.expanduser(options.previous))
            if os.path.basename(filename) != 'ksc-result.txt':
                print "Please point to the ksc-result.txt file in -p option."
                return
            self.submit(filename, path)
            return

        self.releasedir = 'kabi-current'
        choices = { 'rhel6.0': 'kabi-rhel60', 'rhel6.1': 'kabi-rhel61', \
                    'rhel6.2': 'kabi-rhel62', 'rhel6.3': 'kabi-rhel63', \
                    'rhel6.4': 'kabi-rhel64', 'rhel6.5': 'kabi-rhel65', \
                    'rhel6.6': 'kabi-rhel66', 'rhel7.0': 'kabi-rhel70'}
        if options.release in choices:
            self.releasedir = choices[options.release]
        elif not options.release:
            self.releasedir = choices['rhel{0}'.format(get_release_name())]
        else:
            print "You provided invalid kABI release name with -r option."
            return

        if options.ko:
            self.find_arch(options.ko)

        if options.internal:
            self.create_internal(options)
            return

        if options.directory:
            self.find_files(options.directory)
        elif options.ko: # pragma: no cover
            val = self.read_data(self.arch, self.releasedir)
            #Return if there is any issue in reading whitelists
            if not val:
                return
            self.parse_ko(options.ko)
            self.print_result()
            self.save_result([(self.arch,self.white_symbols, self.nonwhite_symbols_used)])
        else: #pragma: no cover
            print "You need to provide a path to a sources directory or .ko file."
            return

        #Now save the result

        if not options.submit:
            return

        if not self.mock: #pragma: no cover
            self.get_justification(filename)
        self.submit(filename, path)


    def input_release_name(self):
        while True:
            self.releasename = raw_input(
                "Please enter valid RHEL release to file bug against: ")
            if self.releasename in self.release_choices:
                break
            else:
                print "Wrong input"


    def create_internal(self, options):
        """
        Creates the text files for internal usage only.
        """
        if get_release_name().split('.')[0] == '7':
            arch_list = ['x86_64', 's390x', 'ppc64']
        else:
            arch_list = ['i686', 'x86_64', 's390x', 'ppc64']

        if options.directory:
            file_list = get_cfiles(options.directory)
            result = []

            for arch in arch_list:
                self.clean()
                self.arch = arch
                val = self.read_data(self.arch, self.releasedir)
                #Return if there is any issue in reading whitelists
                if not val:
                    return
                for f in file_list:
                    self.tmplist = []
                    allsyms = parse_c(f, self.mock)
                    map(self.find_if, allsyms)

                result.append((self.arch, self.nonwhite_symbols_used))
            #now save the result
            self.save_result_internal(result)
        elif options.ko:  # pragma: no cover
            val = self.read_data(self.arch, self.releasedir)
            #Return if there is any issue in reading whitelists
            if not val:
                return
            self.parse_ko(options.ko)
            self.save_result_internal([(self.arch, self.nonwhite_symbols_used)])

    def save_result_internal(self, data):
        "Saves the data in text format for internal usage"

        for datum in data:
            filename = os.path.join(os.path.expanduser("~"), "ksc-internal-%s.yml" % datum[0])
            fobj = open(filename, 'w')
            for name in datum[1]:
                fobj.write('%s: "Enter justification text here."\n' % name)
            fobj.close()
            print filename


    def submit(self, filename, path):
        """
        Submits the resultset into Red Hat bugzilla.

        :arg filename: Full path the ksc-result.txt file.
        :arg path: Path to the config file.
        """
        if not self.mock: #Ask for user permission
            print "By using ksc to upload your data to Red Hat, you consent ", \
                "to Red Hat's receipt use and analysis of this data."
            while True:
                ans = raw_input("y/N: ")
                if ans == 'y':
                    break
                else:
                    return

            if self.releasename is None:
                print "RHEL release not specified with -n flag.", \
                    "Taking RHEL release from system."
                self.releasename = get_release_name()
                print "File bug against RHEL release {0}? ".format(
                    self.releasename)
                while True:
                    ans = raw_input("y/N: ")
                    if ans == 'y':
                        break
                    elif ans == 'N':
                        self.input_release_name()
                        break
                    else:
                        print "Invalid response"

        data = encode_base64(filename)
        createbug(data, self.arch, mock=self.mock, path=path,
                  releasename=self.releasename, filename = filename)


    def get_justification(self, filename):
        """
        Get the justification from User
        on non-whitelist symbols

        """
        bold = "\033[1m"
        reset = "\033[0;0m"

        print bold
        print "On the next screen, the result log will be opened to allow"
        print 'you to provide technical justification on why these symbols need to'
        print 'be included in the KABI whitelist.'
        print 'Please provide sufficient information in the log, marked with the'
        print 'line below:'

        print "\nENTER JUSTIFICATION TEXT HERE\n" + reset
        print bold + 'Press ENTER for next screen.' + reset
        raw_input()

        editor = os.getenv('EDITOR')
        if editor:
            os.system(editor + ' ' + filename)
        else:
            os.system('vi '+ filename)
        return True


    def save_result(self, data):
        """
        Save the result in a text file
        """
        filename = os.path.join(os.path.expanduser("~"),"ksc-result.txt")
        try:
            f = open(filename, "w")
            for i, datum in enumerate(data):
                if i == 0:
                    command = "[command: %s]\n" % " ".join(sys.argv)
                else:
                    command = ""
                self.write_result(f, datum[0], command, datum[1], \
                                    datum[2])
            f.close()
            if not self.mock:
                print "A copy of the report is saved in %s" % filename

        except Exception, e:
            print "Error in saving the result file at %s" % filename
            print e


    def print_result(self):
        """
        Print the result (score)
        """
        total_len = len(set(self.all_symbols_used))
        non_white = len(set(self.nonwhite_symbols_used))
        white_len = float (len(set(self.white_symbols)))

        if total_len == 0: # pragma: no cover
            print "No kernel symbol usage found."
            return

        score = (white_len / total_len) * 100

        if not self.mock:
            print "Checking against architecture %s" % self.arch
            print "Total symbol usage: %s\t"\
                  "Total Non white list symbol usage: %s"\
                  % (total_len, non_white)
            print "Score: %0.2f%%\n" % score



    def find_arch(self, path):
        """
        Finds the architecture of the file in given path
        """
        try:
            rset = {'IBM S/390': 's390x', '64-bit PowerPC or cisco 7500': 'ppc64',
                    'x86-64': 'x86_64'}
            data = run("file %s" % path)
            part = data.split(":")[1].split(",")[1]
            arch = rset.get(part.strip(), 'x86_64')
            self.arch = arch
        except:
            print "Invalid architecture, supported architectures are x86_64,ppc64,s390x"
            sys.exit(1)


    def write_result(self, f, arch, command="", whitelist=[], nonwhitelist=[]):
        """
        Save the result set in the given file
        """
        try:
            if command:
                f.write("%s" % command)
            f.write("[%s]\n" % arch)
            f.write("[WHITELISTUSAGE]\n")
            for name in set(whitelist):
                f.write(name + '\n')
            f.write("[NONWHITELISTUSAGE]\n")
            for name in set(nonwhitelist):
                f.write('#' * 10)
                f.write('\n(%s)\n\nENTER JUSTIFICATION TEXT HERE\n\n' % name)
            if set(nonwhitelist):
                f.write('#' * 10)
                f.write('\n')
        except Exception, err:
            print err


    def read_data(self, arch, releasedir):
        """
        Read both data files
        """
        self.matchdata = read_list(arch, releasedir, self.verbose);
        self.total = read_total_list(arch);
        if self.matchdata == []:
            return False #Means exit now
        return True #Do not exit


    def parse_ko(self, path):
        """
        parse a ko file
        """
        if not os.path.isfile(path):
            print "KO file can not be found"
            return

        out = run("nm -u %s" % path )
        for line in out.split("\n"):
            data = line.split("U ")
            if len(data)  == 2:
                self.find_if(data[1])
        #self.print_tmplist(path)


    def find_if(self, name):
        """
        Find if the symbol is in whitelist or not
        """
        data = name.split('_R')
        if len(data) > 1:
            name = data[1]
        if name in self.matchdata:
            self.white_symbols.append(name)
            self.all_symbols_used.append(name)
        elif name in self.total:
            self.all_symbols_used.append(name)
            self.nonwhite_symbols_used.append(name)
            self.tmplist.append(name)


    def find_files(self, path):
        file_list = get_cfiles(path)
        result = []
        if get_release_name().split('.')[0] == '7':
            arch_list = ['x86_64', 's390x', 'ppc64']
        else:
            arch_list = ['i686', 'x86_64', 's390x', 'ppc64']

        for arch in arch_list:
            self.clean()
            self.arch = arch
            val = self.read_data(self.arch, self.releasedir)
            #Return if there is any issue in reading whitelists
            if not val:
                return

            for f in file_list:
                self.tmplist = []
                allsyms = parse_c(f, self.mock)
                map(self.find_if, allsyms)
                #self.print_tmplist(f)

            self.print_result()
            result.append((self.arch,self.white_symbols, self.nonwhite_symbols_used))
        #now save the result
        self.save_result(result)
        #set the architecture of the bug as no-arch
        self.arch = "noarch"


if __name__ == '__main__':
    k = Ksc()
    k.main()
    sys.exit(0)
