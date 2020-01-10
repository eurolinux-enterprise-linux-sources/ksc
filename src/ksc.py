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
import re
import sys
from optparse import OptionParser
from utils import run, read_list
from utils import read_total_list, get_cfiles, get_release_name
from utils import createbug
from keywords import endpoints, keywords, parse_c

KSCVERSION = "ksc - Version 0.9.22"


class Ksc(object):
    HEADER_RE = re.compile(r"\[command: (?P<cmd>.*)\]")

    def __init__(self, mock=False):
        """
        Init call
        """
        self.all_symbols_used = []
        self.nonwhite_symbols_used = []
        self.white_symbols = []
        self.matchdata = None
        self.total = None
        self.verbose = False
        self.mock = mock
        self.releasedir = None
        self.symvers = None
        self.arch = None
        if mock:
            self.releasename = '7.0'
        else:
            self.releasename = None

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
        filename = os.path.join(os.path.expanduser("~"), "ksc-result.txt")
        # default architecture
        self.arch = "x86_64"

        parser = OptionParser()
        parser.add_option("-c", "--config", dest="config",
                          help="path to configuration file", metavar="CONFIG")
        parser.add_option("-d", "--directory", dest="directory",
                          help="path to the directory", metavar="DIRECTORY")
        parser.add_option("-i", "--internal", action="store_true",
                          dest="internal",
                          help="to create text files to be used internally ",
                          metavar="INTERNAL")
        parser.add_option("-k", "--ko", action="append", dest="ko",
                          help="path to the ko file", metavar="KO")
        parser.add_option("-n", "--name", dest="releasename",
                          help="Red Hat release to file the bug against, "
                               "e.g '6.7'", metavar="RELEASENAME")
        parser.add_option("-p", "--previous", dest="previous",
                          help="path to previous resultset to submit as bug")
        parser.add_option("-r", "--release", dest="release",
                          help="RHEL whitelist release to compare against, "
                               "e.g '6.7'", metavar="RELEASE")
        parser.add_option("-y", "--symvers", dest="symvers",
                          help="Path to the Module.symvers file. "
                               "The current kernel path is used if "
                               "not specified.",
                          metavar="SYMVERS")
        parser.add_option("-s", "--submit",
                          action="store_true", dest="submit", default=False,
                          help="Submit to Red Hat Bugzilla")
        parser.add_option("-v", "--version",
                          action="store_true", dest="VERSION", default=False,
                          help="Prints KSC version number")

        if not self.mock:  # pragma: no cover
            (options, args) = parser.parse_args(sys.argv[1:])
        else:  # pragma: no cover
            (options, args) = parser.parse_args(mock_options)

        if options.VERSION:
            print KSCVERSION
            sys.exit(0)

        # Create the ksc.conf config path
        if options.config:
            path = os.path.abspath(os.path.expanduser(options.config))
        else:
            path = os.path.expanduser("~/ksc.conf")

        if options.releasename:
            self.releasename = options.releasename
            if not self.valid_release_version(self.releasename):
                sys.exit(1)

        if options.release:
            if not self.valid_release_version(options.release):
                sys.exit(1)

        if options.releasename and options.release and \
                        options.release != options.releasename:
            print "Release and release name do not match."
            sys.exit(1)

        if options.previous:  # Submit the result of previous run
            filename = os.path.abspath(os.path.expanduser(options.previous))
            if os.path.basename(filename) != 'ksc-result.txt':
                print "Please point to the ksc-result.txt file in -p option."
                sys.exit(1)

            self.submit(filename, path)
            return

        self.releasedir = 'kabi-current'
        if options.release:
            if not self.valid_release_version(options.release):
                sys.exit(1)

            self.releasedir = 'kabi-rhel' + options.release.replace('.', '')

        if options.symvers:
            self.symvers = options.symvers

        if options.ko:
            if len(options.ko) > 1:
                print "Option -k can be specified only once."
                sys.exit(1)
            self.find_arch(options.ko[0])

        if options.internal:
            self.create_internal(options)
            return

        if options.directory:
            self.find_files(options.directory)
        elif options.ko:  # pragma: no cover
            exists = self.read_data(self.arch, self.releasedir, self.symvers)
            # Return if there is any issue in reading whitelists
            if not exists:
                print("Release %s for arch %s was not found.\n"
                      "Do you have right kernel-abi-whitelist installed ?" %
                      (self.releasedir, self.arch))
                sys.exit(1)
            self.parse_ko(options.ko[0])
            self.print_result()
            self.save_result([(self.arch, self.white_symbols,
                               self.nonwhite_symbols_used)])
        else:  # pragma: no cover
            print ("You need to provide a path to a sources directory or "
                   ".ko file.")
            sys.exit(1)

        # Now save the result

        if not options.submit:
            return

        if not self.mock:  # pragma: no cover
            self.get_justification(filename)
        self.submit(filename, path)

    def valid_release_version(self, release):
        rels = release.split(".")
        if len(rels) != 2:
            print "Invalid release: %s" % release
            return False
        if not rels[0].isdigit() or int(rels[0]) <= 5:
            print "Invalid release: %s" % release
            return False
        return True

    def input_release_name(self):
        while True:
            self.releasename = raw_input(
                "Please enter valid RHEL release to file bug against: ")
            if self.valid_release_version(self.releasename):
                break
            else:
                print "Wrong input"

    def create_internal(self, options):
        """
        Creates the text files for internal usage only.
        """
        release = get_release_name()
        if not release:
            sys.exit(1)
        major = release.split('.')[0]

        if int(major) >= 7:
            arch_list = ['x86_64', 's390x', 'ppc64', 'ppc64le', 'aarch64']
        else:
            arch_list = ['i686', 'x86_64', 's390x', 'ppc64']

        if options.directory:
            file_list = get_cfiles(options.directory)
            result = []

            for arch in arch_list:
                self.clean()
                self.arch = arch
                _ = self.read_data(self.arch, self.releasedir, self.symvers)
                for f in file_list:
                    allsyms = parse_c(f, self.mock)
                    map(self.find_if, allsyms)

                result.append((self.arch, self.nonwhite_symbols_used))
            # now save the result
            self.save_result_internal(result)
        elif options.ko:  # pragma: no cover
            exists = self.read_data(self.arch, self.releasedir, self.symvers)
            # Return if there is any issue in reading whitelists
            if not exists:
                sys.exit(1)

            self.parse_ko(options.ko[0])
            self.save_result_internal([(self.arch,
                                        self.nonwhite_symbols_used)])

    def save_result_internal(self, data):
        "Saves the data in text format for internal usage"

        for datum in data:
            filename = os.path.join(os.path.expanduser("~"),
                                    "ksc-internal-%s.yml" % datum[0])
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
        try:
            with open(filename, "r") as fptr:
                line = fptr.readline().strip()
                module_name = self.get_module_name(line)
        except IOError as err:
            print "Unable to read previous result: {}".format(err)
            sys.exit(1)

        if not self.mock:  # Ask for user permission
            print ("By using ksc to upload your data to Red Hat, you consent "
                   "to Red Hat's receipt use and analysis of this data.")
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
                if not self.releasename:
                    sys.exit(1)

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

        createbug(filename, self.arch, mock=self.mock, path=path,
                  releasename=self.releasename, module=module_name)

    def get_justification(self, filename):
        """
        Get the justification from User
        on non-whitelist symbols

        """
        bold = "\033[1m"
        reset = "\033[0;0m"

        print bold
        print 'On the next screen, the result log will be opened to allow'
        print 'you to provide technical justification on why these symbols'
        print 'need to be included in the KABI whitelist.'
        print 'Please provide sufficient information in the log, marked with '
        print 'the line below:'

        print "\nENTER JUSTIFICATION TEXT HERE\n" + reset
        print bold + 'Press ENTER for next screen.' + reset
        raw_input()

        editor = os.getenv('EDITOR')
        if editor:
            os.system(editor + ' ' + filename)
        else:
            os.system('vi ' + filename)
        return True

    def save_result(self, data):
        """
        Save the result in a text file
        """
        output_filename = os.path.expanduser("~/ksc-result.txt")
        if os.path.isfile(output_filename):
            res = raw_input("ksc-result.txt already exists. Do you want to "
                            "overwrite it ? [y/N]: ")
            if not (res and res[0].lower() == 'y'):
                print "User interrupt"
                sys.exit(-1)
        try:
            f = open(output_filename, "w")
            for i, datum in enumerate(sorted(data)):
                if i == 0:
                    command = "[command: %s]\n" % " ".join(sys.argv)
                else:
                    command = ""
                self.write_result(f, datum[0], command, datum[1],
                                  datum[2])
            f.close()
            if not self.mock:
                print "A copy of the report is saved in %s" % output_filename

        except Exception as e:
            print "Error in saving the result file at %s" % output_filename
            print e

    def print_result(self):
        """
        Print the result (score)
        """
        total_len = len(set(self.all_symbols_used))
        non_white = len(set(self.nonwhite_symbols_used))
        white_len = float(len(set(self.white_symbols)))

        if total_len == 0:  # pragma: no cover
            print "No kernel symbol usage found."
            return

        score = (white_len / total_len) * 100

        if not self.mock:
            print "Checking against architecture %s" % self.arch
            print "Total symbol usage: %s\t" \
                  "Total Non white list symbol usage: %s" \
                  % (total_len, non_white)
            print "Score: %0.2f%%\n" % score

    def find_arch(self, path):
        """
        Finds the architecture of the file in given path
        """
        rset = {'littleendianIntel80386' : 'i686',
                'bigendianPowerPC64' : 'ppc64',
                'littleendianPowerPC64' : 'ppc64le',
                'littleendianAdvancedMicroDevicesX86-64' : 'x86_64',
                'bigendianIBMS/390' : 's390x',
                'littleendianAArch64' : 'aarch64'}
        try:
            data = run("readelf -h %s | grep -e Data -e Machine | awk -F "
                       "':' '{print $2}' | paste -d ' '  - - | awk -F ',' "
                       "'{print $2}' | sed 's/[ \t]*//g'" % path)
            arch = rset[data.strip()]
            self.arch = arch
        except IOError as e:
            print e,
            print ("(Only kernel object files are supported)") \
                if "No such file" not in e.message \
                else ""
            sys.exit(1)
        except KeyError:
            print "%s: Invalid architecture. (only %s are supported)" \
                  % (path, ', '.join(sorted(rset.values())))
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
            for name in sorted(set(whitelist)):
                f.write(name + '\n')
            f.write("[NONWHITELISTUSAGE]\n")
            for name in sorted(set(nonwhitelist)):
                f.write('#' * 10)
                f.write('\n(%s)\n\nENTER JUSTIFICATION TEXT HERE\n\n' % name)
            if set(nonwhitelist):
                f.write('#' * 10)
                f.write('\n')
        except Exception as err:
            print err

    def read_data(self, arch, releasedir, symvers):
        """
        Read both data files
        """
        self.matchdata, exists = read_list(arch, releasedir, self.verbose)
        self.total = read_total_list(symvers)
        return exists

    def parse_ko(self, path):
        """
        parse a ko file
        """
        try:
            out = run("nm -u '%s'" % path)
        except Exception as e:
            print e
            sys.exit(1)
        for line in out.split("\n"):
            data = line.split("U ")
            if len(data) == 2:
                self.find_if(data[1])

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
        else:
            self.all_symbols_used.append(name)
            self.nonwhite_symbols_used.append(name)
            if name not in self.total:
                print "WARNING: External symbol does not exist in current " \
                      "kernel: %s" % name

    def find_files(self, path):
        file_list = get_cfiles(path)
        result = []
        release = get_release_name()
        if not release:
            sys.exit(1)

        major = release.split('.')[0]

        if int(major) >= 7:
            arch_list = ['x86_64', 's390x', 'ppc64', 'ppc64le', 'aarch64']
        else:
            arch_list = ['i686', 'x86_64', 's390x', 'ppc64']

        for arch in arch_list:
            self.clean()
            self.arch = arch
            _ = self.read_data(self.arch, self.releasedir, self.symvers)

            for f in file_list:
                allsyms = parse_c(f, self.mock)
                map(self.find_if, allsyms)

            self.print_result()
            result.append((self.arch, self.white_symbols,
                           self.nonwhite_symbols_used))
        # now save the result
        self.save_result(result)
        # set the architecture of the bug as no-arch
        self.arch = "noarch"

    def get_module_name(self, command_line):
        try:
            match = self.HEADER_RE.match(command_line)
            if not match:
                return None
            commands = match.group("cmd").split()

            # Ignore undefined options in parser instead of throwing error
            class IOptParse(OptionParser):
                def error(self, msg):
                    pass

            parser = IOptParse()
            parser.add_option("-d", "--directory")
            parser.add_option("-k", "--ko")
            opts, _ = parser.parse_args(commands[0:])
            return opts.directory or opts.ko
        except Exception:
            return None


if __name__ == '__main__':
    k = Ksc()
    k.main()
    sys.exit(0)
