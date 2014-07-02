""" This is just an example fedmsg config file to be used
during development of anitya.
"""

import socket
hostname = socket.gethostname().split('.')[0]

config = dict(
    endpoints={
        "relay_outbound": ["tcp://127.0.0.1:4011"],
        "anitya.%s" % hostname: [
            "tcp://127.0.0.1:5011",
            "tcp://127.0.0.1:5012",
            "tcp://127.0.0.1:5013",
        ],
    },

    relay_inbound="tcp://127.0.0.1:2013",
    environment="dev",
    high_water_mark=0,
    io_threads=1,
    post_init_sleep=0.2,
    irc=[],
    zmq_enabled=True,
    zmq_strict=False,

    sign_messages=False,
    validate_messages=False,
)
