#!/usr/bin/env python

import json
import logging
from os import environ as env
from urllib.parse import urljoin
from requests import request, exceptions
from argparse import ArgumentParser, RawTextHelpFormatter

HELP_DEFINITION='''
Script to initiate Gitea organizations.
'''
HELP_EXAMPLE='''
Example:
\n\t./init-regisitry-org.py \
  --log-level=info \
  --orgs=org1,org2,org3 \
  --gitea-url=https://example.com/gitea/api/v1/ \
  --gitea-token=username
'''

headers= {
    'Content-type': 'application/json'
}

class Gitea:

    def __init__(self, url, token):
        self.url = url
        self.token = token

    def _request(self, method, path, data=None):
        url = urljoin(self.url, path)
        headers = { 'Authorization': 'token ' + self.token }
        logging.debug('Request: %s %s - %s', method, path, json)
        try:
            result = request(
                method=method,
                url=url,
                json=data,
                headers=headers,
            )
        except exceptions.ConnectionError as e:
            logging.error('ConnectionError on url %s: %s', url, e)
            return None
        if result.status_code == 404:
            result.raise_for_status()
        if result.status_code not in [200, 201, 404]:
            logging.error('Request failed: %s %s (%d)', method, url, result.status_code)
            logging.error('Error: %s', result.text)
            result.raise_for_status()
        return result

    def create_org(self, org, vis='limited'):
        return self._request('POST', 'orgs', {'visibility':vis,'username':org})


def parse_args():
    parser = ArgumentParser(description=HELP_DEFINITION, epilog=HELP_EXAMPLE, formatter_class=RawTextHelpFormatter)
    parser.add_argument('-o', '--orgs',        help='List of organization to create in Gitea. Separate each value with ","', required=True)
    parser.add_argument('-l', '--log-level',   help='Select log level', default='INFO')
    parser.add_argument('-t', '--gitea-token', help='Gitea API token.', default=env.get('GITEA_TOKEN'))
    parser.add_argument('-u', '--gitea-url',   help='Gitea API URL.',   default=env.get('GITEA_URL', 'http://127.0.0.1:3000/api/v1/'))
    args = parser.parse_args()

    assert args.gitea_token, parser.error('No API token provided!')

    return args


def main():
    args = parse_args()
    logging.basicConfig(level=args.log_level.upper())

    gitea = Gitea(args.gitea_url, args.gitea_token)

    for org in args.orgs.split(','):
        try:
            logging.info('Creating org %s', org)
            gitea.create_org(org)
        except exceptions.HTTPError as ex:
            if 'user already exists' in ex.response.text:
                logging.info('Org %s already exists', org)

if __name__ == '__main__':
    main()
