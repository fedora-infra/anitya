""" This is just an example fedmsg config file to be used
during development of anitya.
"""

config = {
    "zmq_enabled": True,
    "active": True,
    "endpoints": {"relay_outbound": ["tcp://127.0.0.1:4011"]},
    "relay_inbound": "tcp://127.0.0.1:2013",
    "environment": "dev",
    "sign_messages": False,
    "validate_signatures": False,
    "anitya.libraryio.enabled": True,
}
