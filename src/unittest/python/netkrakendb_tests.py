from __future__ import print_function

from collections import namedtuple

import unittest
from mock import patch, MagicMock, mock_open, call

import netkraken
from netkraken.db import Fetcher, Aggregator
import countdb


class NetKrakenTests(unittest.TestCase):

    def setUp(self):
        netkraken.settings = {"stagedir": "///invalid///",
                              "finaldir": "///invalid///"}
        self.current_timestrings = {'day': '2042-12-12',
                                    'minute': '2042-12-12T12:12',
                                    'hour': '2042-12-12T12'}

    @patch("psutil.net_connections")
    @patch("netkraken.db.get_current_timestrings")
    def test_fetch(self, current_timestrings, net_connections):
        current_timestrings.return_value = self.current_timestrings
        Connection = namedtuple("sconn", "laddr raddr status pid")
        net_connections.return_value = [
            Connection(laddr=('bar', 443), raddr=(), status='LISTEN', pid=55424),
            Connection(laddr=('foo', 12345), raddr=('bar', 443), status='ESTABLISHED', pid=1),
            Connection(laddr=('127.0.0.1', 50314), raddr=('127.0.0.1', 54283), status='ESTABLISHED', pid=55424),
            Connection(laddr=('127.0.0.1', 54283), raddr=('127.0.0.1', 50314), status='ESTABLISHED', pid=55386)]
        countdb.makedirs = MagicMock(name="makedirs")

        f = Fetcher()
        m = mock_open()
        with patch("countdb.CountDB._open_file", m, create=True):
            f.fetch()
        m.assert_has_calls([call().write('"foo bar 443"')])

    @patch("glob.glob")
    def test_aggregate(self, globglob):
        netkraken.db.print = netkraken.db.makedirs = countdb.makedirs = MagicMock()
        globglob.return_value = ("2000-01-01T01:01", "2042-12-12T12:12", "2042-12-12T12:13")

        m = mock_open(read_data='{"counter": 13, "data": {"foo bar braz": 39, "ham egg mont": 13}}')
        with patch("countdb.CountDB._open_file", m, create=True):
            a = Aggregator()

            a.finalize = MagicMock()
            a.remove = MagicMock()
            a.aggregate()

            a.finalize.assert_has_calls([call("2042-12-12T12:12"), call("2042-12-12T12:13")])
            a.remove.assert_has_calls([call("2000-01-01T01:01"), call("2000-01-01T01:01")])


if __name__ == "__main__":
    unittest.main()
