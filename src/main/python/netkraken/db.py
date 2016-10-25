#!/usr/bin/env python
from __future__ import print_function

from datetime import datetime
import glob
import os
import shutil

import psutil

from netkraken import (settings,
                       formats,
                       thresholds,
                       get_current_timestrings,
                       get_timestamp,
                       get_higher_timestamp,
                       get_stage_filename,
                       get_final_filename)
from countdb import CountDB, makedirs


class Fetcher(object):
    def __init__(self):
        self.timestamp = get_current_timestrings()["minute"]
        self.filename = get_stage_filename(self.timestamp)

    def fetch(self):
        counted = 0
        with CountDB.open_for_counting(self.filename) as db:
            connections = psutil.net_connections(kind="inet4")

            listening = set([connection.laddr[1] for connection in connections
                             if connection.status == psutil.CONN_LISTEN])

            for connection in connections:
                if connection.status in (psutil.CONN_NONE, psutil.CONN_LISTEN):
                    continue
                local_host, local_port = connection.laddr
                if local_port in listening:
                    continue  # ignore incoming connections completely
                source = connection.laddr
                target = connection.raddr

                try:
                    # import socket
                    # source_host = socket.gethostbyaddr(source[0])[0]
                    # target_host = socket.gethostbyaddr(target[0])[0]
                    source_host = source[0]
                    target_host = target[0]
                    if source_host in ("127.0.0.1") or target_host in ("127.0.0.1"):
                        continue
                    db.count(" ".join([source_host, target_host, str(target[1])]))
                    counted += 1
                except:
                    print("ERROR parsing: %s" % str(connection))
                    raise
        print("%i connections counted" % counted)

    def dump(self):
        with CountDB.open(self.filename) as db:
            db.dump()


class Aggregator(object):
    def __init__(self):
        self.current = get_current_timestrings()

    def aggregate(self):
        for filename in sorted(glob.glob(os.path.join(settings["stagedir"], "*")), key=len, reverse=True):
            level, timestamp = get_timestamp(filename)
            # print("stage: %s [%s]" % (filename, level))

            if self.is_current(level, timestamp):
                # print("\tis current, ignoring for now")
                continue

            if self.is_too_old(level, timestamp):
                # print("\ttoo old, ignoring")
                self.remove(filename)
                continue

            higher_level, higher_timestamp = get_higher_timestamp(filename)
            # print("\thigher level: %s [%s]" % (higher_timestamp, higher_level))
            if not higher_level:
                continue

            if self.is_finalized(higher_timestamp):
                # print("\t%s slot %s already finalized, ignoring" % (higher_level, higher_timestamp))
                self.remove(filename)
                continue

            # from here: filename is not current, not already finalized, not too old
            self.aggregate_file(filename, higher_timestamp)
            self.finalize(filename)

        for filename in sorted(glob.glob(os.path.join(settings["finaldir"], "*"))):
            level, timestamp = get_timestamp(filename)
            # print("final: %s [%s]" % (filename, level))
            if self.is_too_old(level, timestamp):
                # print("\ttoo old, removing")
                self.remove(filename)

    def finalize(self, filename):
        final_filename = get_final_filename(filename)
        # print("finalize %s -> %s" % (filename, final_filename))
        # use finalize() on CountDB
        makedirs(final_filename)
        # shutil.move(filename, final_filename)
        with CountDB.open(filename) as db:
            db.finalize(final_filename)

    def aggregate_file(self, filename, timestamp):
        higher_stage_filename = get_stage_filename(timestamp)
        # print("aggregating in %s" % higher_stage_filename)
        with CountDB.open_for_extending(higher_stage_filename) as aggregated_db:
            with CountDB.open(filename) as db:
                aggregated_db.extend(db)

    def is_too_old(self, level, timestamp):
        current_dt = datetime.strptime(self.current[level], formats[level])
        timestamp_dt = datetime.strptime(timestamp, formats[level])
        delta = current_dt - timestamp_dt
        return delta > thresholds[level]

    def is_current(self, level, timestamp):
        return self.current[level] == timestamp

    def is_finalized(self, timestamp):
        higher_final_filename = get_final_filename(timestamp)
        return os.path.exists(higher_final_filename)

    def remove(self, filename):
        # print("\tremoving")
        shutil.move(filename, os.path.join("/tmp", os.path.basename(filename)))
        # os.remove(filename)
