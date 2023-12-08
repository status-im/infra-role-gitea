#!/usr/bin/env python

from argparse import ArgumentParser, RawTextHelpFormatter
from os import environ
import datetime
import json
import logging
import requests

HELP_DEFINITION='''
Script to initiate Gitea Image registry organization
'''
HELP_EXAMPLE='''
Example:
\n\t./purge-registry.py \
  --url https://example.com/gitea \
  --user admin \
  --password password123 \
  --retention 5
'''

DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

class Artifact:

    def __init__(self, name, owner, creation_date, version):
        self.name           = name
        self.owner          = owner
        self.creation_date  = datetime.datetime.strptime(creation_date, DATE_FORMAT)
        self.version        = version
 
    def should_be_purge(self, retention_time):
        if (self.creation_date + datetime.timedelta(days=retention_time)) < datetime.datetime.now() :
            return True
        else:
            logging.info('The artifact %s is %s old' % (self.name, abs((datetime.datetime.now() - self.creation_date))))
            return False

class GiteaApi:
    def __init__(self, url, username, password):
        self.url = url
        self.auth = requests.auth.HTTPBasicAuth(username, password)
    
    def _req(self, method, path):
        try:
            rval = requests.request(method, self.url+path, auth=self.auth)
            rval.raise_for_status()
            return rval
        except Exception as ex:
            logging.error(rval.text)
            raise ex

    def _get(self, path):
        return self._req('GET', path)

    def _del(self, path):
        return self._req('DELETE', path)

def get_organization(giteaApi):
    logging.info('Querrying all the organization')
    try:
        orgs=[]
        res=giteaApi._get('orgs')
        for elt in res.json():
            orgs.append(elt['username'])
        return orgs
    except requests.exceptions.HTTPError as err:
        logging.error('Error %s when trying to get the organization: %s' % (err.response.status_code, err.response.text))

def get_artifacts(giteaApi, org):
    logging.info('Querrying org %s to list all artifacts' % org)
    try:
        arts=[]
        res=giteaApi._get('packages/%s' %  org)
        for elt in res.json():
            if elt['type'] == 'container':
                arts.append(Artifact(elt['name'], elt['owner'], elt['created_at'], elt['version']))
        return arts
    except requests.exceptions.HTTPError as err:
        logging.error('Error %s when trying to get all the artifact of %s: %s' % (err.response.status_code, org, err.response.text))
        raise err

def delete_artifact(giteaApi, art):
    logging.info('Deleting artifact %s of %s' % (art.name, art.owner))
    try:
        res=giteaApi._del('packages/%s/container/%s/%s' % (art.owner, art.name, art.version))
    except requests.exceptions.HTTPError as err:
        logging.error('Error %s when trying to delete artifact %s:%s from %s: %s' % (err.response.status_code, art.name, art.version, art.owner, err.response.text))
        raise err

def parse_args():
    parser = ArgumentParser(description=HELP_DEFINITION, epilog=HELP_EXAMPLE, formatter_class=RawTextHelpFormatter)
    parser.add_argument('-r', '--retention',  required=True,  type=int, help='Maximum retention period for each artifact in days')
    parser.add_argument('-U', '--url',        required=True,  help='URL of the Gitea instance')
    parser.add_argument('-u', '--username',   default=environ.get('GITEA_USERNAME'), help='Gitea API Username')
    parser.add_argument('-p', '--password',   default=environ.get('GITEA_PASSWORD'),  help='Gitea API Password')
    parser.add_argument('-l', '--log',        required=False, default='INFO')
    args = parser.parse_args()
    assert args.username and args.password, parser.error('No API username or password!')
    return args

def main():
    args = parse_args()
    logging.basicConfig(level=args.log.upper())
    giteaApi = GiteaApi('%s/api/v1/' % args.url, args.username, args.password)
    orgs=get_organization(giteaApi)
    logging.info("Deployment : %s", orgs)
    failed=[]
    for org in orgs:
        logging.info('Get containers from %s' % org)
        try:
            conts = get_artifacts(giteaApi, org)
            for cont in conts:
                if not cont.should_be_purge(args.retention):
                    continue
                try:
                    delete_artifact(giteaApi, cont)
                except requests.exceptions.HTTPError as err:
                    failed.append(err.response.text)
        except requests.exceptions.HTTPError as err:
            failed.append(err.response.text)
    if len(failed) > 0:
        logging.error('The purge has failed:\n%s' % failed)
        exit(1)
if __name__ == '__main__':
  main()
