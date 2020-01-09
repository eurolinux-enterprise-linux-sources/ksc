import unittest
import os
from utils import *
from keywords import *
from ksc import Ksc
import xmlrpclib
from mock import Mock, patch


class SetTest(unittest.TestCase):
    """
    To test the set operation
    """
    def runTest(self):
        l = ksc_set([1, 2, 3, 4, 1, 2, 3, 2])
        assert len(l) == 4


class WalkTest(unittest.TestCase):
    """
    To test ksc walk function
    """
    def runTest(self):
        x = ksc_walk('./data')
        x = x[0][2]
        assert 'ksc.conf' in x


class ReadListTest(unittest.TestCase):
    """
    Test reading whitelist
    """
    def runTest(self):
        data = read_list("x86_64", "kabi-current")
        assert len(data) != 0


class ReadTotalListTest(unittest.TestCase):
    """
    Test reading all symbol names
    """
    def runTest(self):
        data = read_total_list()
        assert len(data) != 0


class MyfileTest(unittest.TestCase):
    """
    To test the internal file like object
    """
    def runTest(self):
        mf = Myfile()
        mf.write("hello")
        assert "hello" == mf.read()


class FindCTest(unittest.TestCase):
    """
    To test finding C source code files
    """
    def runTest(self):
        data = get_cfiles('./data')
        assert len(data) == 1


class KeywordsTest(unittest.TestCase):
    """
    To view the keywords
    """
    def runTest(self):
        import keywords
        assert 'break' in keywords.keywords
        assert 'register' in keywords.keywords


class ParseCTest(unittest.TestCase):
    """
    To parse the C code
    """
    def runTest(self):
        data = parse_c('data/test.c')
        assert set(['printf', 'add_disk', 'add_drv', 'call_rcu_bh']) == data


class ParseCfailTest(unittest.TestCase):
    """
    To test our own set function
    """
    def runTest(self):
        data = parse_c('data/does_not_exists.c', True)
        assert [] == data


class RunCommandTest(unittest.TestCase):
    """
    To test our own set function
    """
    def runTest(self):
        data = run('uname -a')
        self.assertTrue(data.startswith('Linux'))


class GetConfigTest(unittest.TestCase):
    """
    To test our own set function
    """
    def runTest(self):
        data = getconfig('./data/ksc.conf', True)
        assert 'user' in data
        assert 'partner' in data
        assert 'group' in data
        assert 'server' in data


class CreateBugTest(unittest.TestCase):
    """
    Code to test createbug function
    """
    def runTest(self):
        bugid = createbug('./data/ksc.conf', 'x86_64', True)  # This is mock
        self.assertEqual(bugid, 0)


class KSCTest(unittest.TestCase):
    """
    Code to test the main workflow class
    """
    @patch('xmlrpclib.Server')
    def runTest(self, mock_server):
        s = mock_server.return_value
        s.Bug.create.return_value = {'id': 110}
        s.bugzilla.addAttachment.return_value = True
        k = Ksc(mock=True)
        k.main(['-r', '6.2', '-s', '-d', './data/'])


class ParseKOTest(unittest.TestCase):
    """
    Code to test parse_ko
    """
    @patch('ksc.run')
    def runTest(self, mock_run):
        mock_run.return_value = 'U add_disk\nU add_drv\nU call_rcu_bh'
        k = Ksc(mock=True)
        k.read_data('x86_64', 'kabi-current')
        k.parse_ko('./ksc.py')
        assert len(k.all_symbols_used) == 2
        assert len(k.nonwhite_symbols_used) == 1
        assert len(k.white_symbols) == 1


if __name__ == '__main__':
    unittest.main()
