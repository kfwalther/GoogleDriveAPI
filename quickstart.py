from __future__ import print_function
import httplib2
import os
from collections import defaultdict
import calendar

import apiclient
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Drive API Python Quickstart'

"""Gets valid user credentials from storage.

If nothing has been stored, or if the stored credentials are invalid,
the OAuth2 flow is completed to obtain the new credentials.

Returns:
    Credentials, the obtained credential.
"""
def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'drive-python-quickstart.json')

    store = Storage(credential_path)
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

# Define a function to get a list of all the photos in the 'Google Photos IphoneSE' folder.
def getAllPhotos(apiService):
    # Get the folder ID of the 'Google Photos IphoneSE' folder.
    googlePhotosFolder = [item for item in (apiService.files().list(
            pageSize = 100, q = "'root' in parents").execute()['files']) if item['name'] == 'Google Photos IphoneSE']
    googlePhotosFolderId = googlePhotosFolder[0]['id']
    allPhotos = []
    page_token = None
    pageCount = 1
    # Loop through all pages of files, saving them in the allPhotos list.
    while True:
        try:
            print('Requesting page #%d...' % pageCount)
            param = {}
            if page_token:
                param['pageToken'] = page_token
            param['q'] = "'%s' in parents" % googlePhotosFolderId
            param['fields'] = "nextPageToken, files(id, name, createdTime)"
            # Request a list of files from the Discovery service.
            files = apiService.files().list(**param).execute()
            # Add the page of files to the list.
            allPhotos.extend(files['files'])
            page_token = files.get('nextPageToken')
            if not page_token:
                break
            pageCount = pageCount + 1
        except apiclient.errors.HttpError, error:
            print('An error occurred: %s' % error)
            break
    return allPhotos

# Define a function to create a folder on Google Drive.
def createRemoteFolder(folderName, apiService, parentID = None):
    # Create a folder on Drive, returns the newly created folders ID
    folderMetadata = {
      'name': folderName,
      'mimeType': "application/vnd.google-apps.folder"
    }
    if parentID:
        folderMetadata['parents'] = [parentID]
    folder = apiService.files().create(body = folderMetadata).execute()
    return folder['id']

# Define a function to separate a list of photos by creation date.
def separatePhotosByMonth(allPhotos):
    monthlyPhotos = defaultdict(list)
    for currentPhoto in allPhotos:
        monthlyPhotos[currentPhoto['createdTime'][0:7]].append(currentPhoto)
    return monthlyPhotos
    
# Define a function to copy the photos by creation date into their respective folders.
def copyPhotosToFolders(apiService, allPhotosByMonth, photosFolderId):
    # Loop through each key in the allPhotosByMonth dictionary.
    for key, value in allPhotosByMonth.iteritems():
        if (key == '2007-09'):
            # If the year folder does not exist, create it.
            yearFolderId = [item['id'] for item in (apiService.files().list(
                    q = ("'" + photosFolderId + "' in parents")).execute()['files']) if item['name'] == key[0:4]]
            if (len(yearFolderId) > 0):
                yearFolderId = yearFolderId[0]
            else:
                print('Creating folder: ' + key[0:4])
                yearFolderId = createRemoteFolder(key[0:4], apiService, photosFolderId) 
            # If the month folder does not exist, create it.
            monthString = calendar.month_name[int(key[5:7])]
            monthFolderId = [item['id'] for item in (apiService.files().list(
                    q = ("'" + yearFolderId + "' in parents")).execute()['files']) if item['name'] == monthString]
            if (len(monthFolderId) > 0):
                monthFolderId = monthFolderId[0]
            else:
                print('Creating folder: ' + monthString)
                monthFolderId = createRemoteFolder(monthString, apiService, yearFolderId) 
            # Check if any photos in the current list need to be added to the list.
            photosToAdd = [item for item in value if item not in (apiService.files().list(
                    q = ("'" + monthFolderId + "' in parents")).execute()['files'])]
            for photo in photosToAdd:
                # Copy the photo to the appropriate month/year folder.
                print('Adding photo: ' + photo['name'])
                apiService.files().update(fileId = photo['id'], addParents = monthFolderId, fields = 'id, parents').execute()
                
                    
"""Shows basic usage of the Google Drive API.

Creates a Google Drive API service object and outputs the names and IDs
for up to 10 files.
"""
def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    # Create the Google Drive API Discovery service object, for interacting with the API.
    service = discovery.build('drive', 'v3', http=http)
    
    # Get list of all photos.
    allPhotos = getAllPhotos(service)
    
    # Print details about the photos found.
    if not allPhotos:
        print('No files found.')
    else:
#         print('Files:')
#         for item in allPhotos:
#             print('{0} ({1}) {2}'.format(item['name'], item['id'], item['createdTime']))
        print(allPhotos[0].keys())
        print('Number of files: ' + str(len(allPhotos)))
    
    # Get the folder ID of the 'Photos' folder.
    photosFolderId = [item for item in (service.files().list(pageSize = 50, q = "'root' in parents").execute()['files']) 
                      if item['name'] == 'Photos'][0]['id']
    # Separate the photos list by month into a dictionary.
    allPhotosByMonth = separatePhotosByMonth(allPhotos)
    # Copy photos to folders.
    copyPhotosToFolders(service, allPhotosByMonth, photosFolderId)
    
#     newFolderId = createRemoteFolder('folder1', service, photosFolderId)
    
    
# Define the main entry point to the program.
if __name__ == '__main__':
    main()
    
    
    
    
    