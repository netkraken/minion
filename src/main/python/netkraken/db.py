#!/usr/bin/env python
from __future__ import print_function

import psutil


def fetch(db):
    counted = 0
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
