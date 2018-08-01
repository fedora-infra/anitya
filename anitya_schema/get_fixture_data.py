"""
Generate fixture data for the tests.

The package and the development dependencies must be installed.
"""

import os
import json

from fedora_messaging import message
import requests
import click

from anitya_schema.tests import FIXTURES_DIR


@click.command()
@click.option("--timeout", default=300, help="Timeout for datagrepper (seconds)")
def get_fixtures(timeout):
    message.load_message_classes()

    for message_class, name in message._class_to_schema_name.items():
        if not message_class.topic or not name.startswith("anitya"):
            print("Skipping {}".format(message_class))
            continue

        try:
            resp = requests.get(
                "https://apps.fedoraproject.org/datagrepper/raw",
                params={"topic": message_class.topic, "rows_per_page": 5},
                timeout=timeout,
            )
        except requests.exceptions.Timeout:
            print("Datagrepper timed out, maybe there aren't any recent results")
            continue
        if resp.status_code != 200:
            print(
                "Failed to communicate with datagrepper ({})".format(resp.status_code)
            )
            continue

        path = os.path.join(FIXTURES_DIR, message_class.topic + ".json")
        messages = [msg["msg"] for msg in resp.json()["raw_messages"]]
        with open(path, "w") as fp:
            json.dump(messages, fp, sort_keys=True, indent=4)


if __name__ == "__main__":
    get_fixtures()
