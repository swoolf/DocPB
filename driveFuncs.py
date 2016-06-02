import quickstart
import httplib2
import os
import urllib2

from apiclient import discovery
from apiclient.http import MediaFileUpload

#Initialize GoogleDrive
credentials = quickstart.get_credentials()
http = credentials.authorize(httplib2.Http())
service = discovery.build('drive', 'v3', http=http)

def containsPrints(folder):   
    for filename in os.listdir(folder):
        if filename.endswith(".jpg"):
            return True 
    else:
        return False 

def internet_on():
    try:
        response=urllib2.urlopen('http://www.google.com',timeout=1)
        return True
    except urllib2.URLError as err: pass
    return False

def save2drive(filePath, fileName, folderID):
    file_metadata = {
    'name' : fileName,
    'parents': [ folderID ]
        }
    media = MediaFileUpload(filePath,
                        mimetype='image/jpeg',
                        resumable=True)
    file = service.files().create(body=file_metadata,
                                    media_body=media,
                                    fields='id').execute()
    return 

def folderSearch(folderName):
    folderID=''
    page_token = None
    while True:
        response = service.files().list(q="mimeType='application/vnd.google-apps.folder'",
                                             spaces='drive',
                                             fields='nextPageToken, files(id, name)',
                                             pageToken=page_token).execute()
        for file in response.get('files', []):
            # Process change
            if file.get('name')==folderName: folderID = file.get('id')
#            print 'Found file: %s (%s)' % (file.get('name'), file.get('id'))
        page_token = response.get('nextPageToken', None)
        if page_token is None:    
            return folderID
        
def insertFolder(name, parentID): 
    if parentID =='':
         file_metadata = {
      'name' : name,
      'mimeType' : 'application/vnd.google-apps.folder'
        }
    else:       
        file_metadata = {
          'name' : name,
          'mimeType' : 'application/vnd.google-apps.folder',
          'parents'  :  [ parentID ]
        }

    file = service.files().create(body=file_metadata,
                                        fields='id').execute()
    return file.get('id')

