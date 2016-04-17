from __future__ import print_function
import glob
import httplib2
import io
import os
import re

from apiclient import discovery, errors
from apiclient.http import MediaIoBaseDownload
import oauth2client
from oauth2client import client
from oauth2client import tools

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive.readonly'
CLIENT_SECRET_FILE = os.path.expanduser('~/Downloads/client_id.json')
APPLICATION_NAME = 'Drive API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'drive-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def initialize():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)
    return credentials, http, service


def list_files((credentials, http, service)):
    """Shows basic usage of the Google Drive API.

    Creates a Google Drive API service object and outputs the names and IDs
    for up to 10 files.
    """
    credentials, http, service = initialize()
    nextPageToken = None
    while True:
        print('.')
        results = service.files().list(
            pageSize=1000,fields="nextPageToken, files(id, name)",
            pageToken=nextPageToken).execute()
        items = results.get('files', [])
        if not items:
            print('No files found.')
        else:
            for item in items:
                yield item['name'], item['id']
        nextPageToken = results.get('nextPageToken')
        if not nextPageToken:
            break

def get_files():
    credentials, http, service = initialize()
    fntemplate = '/Users/alx/src/drive/python_files/%s-%s'
    for fileName, fileId in list_files((credentials, http, service)):
        savepath = fntemplate % (fileId, fileName)
        if fileName.endswith('.py') and (not os.path.isfile(savepath)):
            print('downloading', fileId, fileName)
            request = service.files().get_media(fileId=fileId)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while True:
                try:
                    status, done = downloader.next_chunk()
                except errors.HttpError:
                    done = True
                    fh.write('\n###############################################################################\nFile truncated during download\n')
                if done:
                    break
            o = open(savepath, 'w')
            o.write(fh.getvalue())
            o.close()

if __name__ == '__main__':
    get_files()
