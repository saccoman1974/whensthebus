import argparse
import datetime
import urllib
import json
import os
import queue
import collections
import multiprocessing
import logging

import requests

DT_NOW = datetime.datetime.now()
DATE_STR_NOW = DT_NOW.strftime("%Y-%m-%d")

LiveBusSchedule = collections.namedtuple(
    "LiveBusSchedule", ["name", "departures"]
)

class BusInfo:
    """Functions that require API access, or process API data."""

    def __init__(
        self, app_id, app_key, api_base="http://transportapi.com/v3/"
    ):
        self.app_id = app_id
        self.app_key = app_key
        self.api_base = api_base
        self.log = logging.getLogger(type(self).__name__)

        if not self.app_id or not self.app_key:
            raise ValueError("Missing app credentials")

    def call_api(self, path, extra_query_params=None):
        """
        Call TransportAPI v3.

        path: A path, relative to api_base, to call.
        extra_query_params: Desired query params other than app_{id,key}.

        Returns a Python object parsed from the API's returned data.
        """

        parsed_url = urllib.parse.urlparse(self.api_base)
        query_params = {"app_id": self.app_id, "app_key": self.app_key}
        if extra_query_params:
            query_params.update(extra_query_params)
        parsed_url = parsed_url._replace(
            query=urllib.parse.urlencode(query_params),
            path=parsed_url.path + path,
        )

        req_obj = requests.get(urllib.parse.urlunparse(parsed_url))
        try:
            return req_obj.json()
        except json.decoder.JSONDecodeError as thrown_exc:
            raise ValueError(
                "Invalid JSON: {}".format(req_obj.text)
            ) from thrown_exc

    def get_next_arrivals(self, bus_stop_id):
        path = f"uk/bus/stop/{bus_stop_id}/live.json"
        data = self.call_api(path)
        arrivals = data.get('departures', {}).get('all', [])
        return arrivals[:10]

def parse_args():
    parser = argparse.ArgumentParser(description='Get live bus arrivals for a specific stop.')
    parser.add_argument('-a', '--atco', type=str, required=True, help='The ATCO code to query.')
    return parser.parse_args()

def main():
    args = parse_args()

    bus = BusInfo(os.getenv("WTB_APP_ID"), os.getenv("WTB_APP_KEY"))
    next_arrivals = bus.get_next_arrivals(args.atco)

    print("Next arrivals for bus stop {}:".format(args.atco))
    for arrival in next_arrivals:
        print(arrival)

if __name__ == "__main__":
    main()