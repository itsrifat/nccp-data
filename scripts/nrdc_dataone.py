#!/usr/bin/env python

'''
This script will download data from nccp server and then upload them into the
Generic Member Node server
'''
from subprocess import call
import os
import time

import sqlite3 as lite

# Stdlib.
import datetime
import hashlib
import logging
import os
import sys
import StringIO

# 3rd party.
import pyxb

# D1.
import d1_common.types.generated.dataoneTypes as dataoneTypes
import d1_common.const
import d1_client.mnclient
import d1_client.data_package


'''
GLOBAL VARIABLES
'''
#NCCP specefic
NCCP_SERVER_PROTOCOL="ftp"
NCCP_SERVER_ADDRESS="sensor.nevada.edu/Aggregated%20Data/Walker%20Basin%20Climate/"
NCCP_SERVER_URL=NCCP_SERVER_PROTOCOL+"://"+NCCP_SERVER_ADDRESS

WGET_LOG_FILE="wget_log.txt"
WGET_FILE_PATTERN="*OneMin*"

NCCP_FILE_IDENTIFIER_PREFIX="NRDC:NCCP:"


DB_LOCATION="nrdc_dataone.db"
TABLE_NAME = 'file_upload_history'

#metadata gen vars
#INFILE_DIR
JAR_FILE_LOC = 'iso19115-xml-gen.jar'
META_OUTFILE_DIR='metadata'
NUMLINES=10
METAFILE_EXT='xml'
INFILE_EXT = 'csv'


#gmn specific

# The path to the files that will be uploaded as science objects.
#SCIENCE_OBJECTS_DIR_PATH = './sensor.nevada.edu'
SCIENCE_OBJECTS_DIR_PATH = '/mnt/nrdc-public-ftp/Aggregated Data/Walker Basin Climate'
# The identifier (PID) to use for the Science Object.
#SCIENCE_OBJECT_PID = 'dataone_test_object_pid'

# The formatId to use for the Science Object. It should be the ID of an Object
# Format that is registered in the DataONE Object Format Vocabulary. A list of
# valid IDs can be retrieved from https://cn.dataone.org/cn/v1/formats.
SYSMETA_FORMATID = 'text/csv'
SYSMETA_FORMATID_METADATA = 'INCITS-453-2009'
RESOURCE_MAP_FORMAT_ID = 'http://www.openarchives.org/ore/terms'
# The DataONE subject to set as the rights holder of the created objects. The
# rights holder must be a subject that is registered with DataONE. Subjects are
# created in the DataONE identity manager at https://cn.dataone.org/cn/portal.
#
# By default, only the rights holder has access to the object, so access to the
# uploaded object may be lost if the rights holder subject is set to a
# non-existing subject or to a subject that is not prepared to handle the
# object.
SYSMETA_RIGHTSHOLDER = 'CN=CA for GMN Client Side Certificates,O=NCCP,C=US,DC=cilogon,DC=org'

# BaseURL for the Member Node. If the script is run on the same server as the
# Member Node, this can be localhost.
MN_BASE_URL = 'https://localhost/mn'
#MN_BASE_URL = 'https://localhost/mn'
CN_ROOT_URL = 'https://cn-stage.test.dataone.org/cn'
# Paths to the certificate and key to use when creating the object. If the
# certificate has the key embedded, the _KEY setting should be set to None. The
# Member Node must trust the certificate and allow access to MNStorage.create()
# for the certificate subject. If the target Member Node is a DataONE Generic
# Member Node (GMN) instance, see the "Using GMN" section in the documentation
# for GMN for information on how to create and use certificates. The information
# there may be relevant for other types of Member Nodes as well.
CERTIFICATE_FOR_CREATE = '/var/local/dataone/certs/client/client_cert_local.pem'
CERTIFICATE_FOR_CREATE_KEY = '/var/local/dataone/certs/client/client_key_nopassword_local.pem'

'''
This function creates an object in the member node
'''
def create_science_object_on_member_node(client, pid,file_path,formatId):
  #pid = NCCP_FILE_IDENTIFIER_PREFIX+os.path.basename(file_path)
  sci_obj = open(file_path, 'rb').read()
  sys_meta = generate_system_metadata_for_science_object(pid, formatId,
                                                         sci_obj)
  client.create(pid, StringIO.StringIO(sci_obj), sys_meta)


def generate_system_metadata_for_science_object(pid, format_id, science_object):
  size = len(science_object)
  md5 = hashlib.md5(science_object).hexdigest()
  now = datetime.datetime.now()
  sys_meta = generate_sys_meta(pid, format_id, size, md5, now)
  return sys_meta



def generate_sys_meta(pid, format_id, size, md5, now):
  sys_meta = dataoneTypes.systemMetadata()
  sys_meta.identifier = pid
  sys_meta.formatId = format_id
  sys_meta.size = size
  sys_meta.rightsHolder = SYSMETA_RIGHTSHOLDER
  sys_meta.checksum = dataoneTypes.checksum(md5)
  sys_meta.checksum.algorithm = 'MD5'
  sys_meta.dateUploaded = now
  sys_meta.dateSysMetadataModified = now
  sys_meta.accessPolicy = generate_public_access_policy()
  return sys_meta



def generate_public_access_policy():
  accessPolicy = dataoneTypes.accessPolicy()
  accessRule = dataoneTypes.AccessRule()
  accessRule.subject.append(d1_common.const.SUBJECT_PUBLIC)
  permission = dataoneTypes.Permission('read')
  accessRule.permission.append(permission)
  accessPolicy.append(accessRule)
  return accessPolicy


'''
This function downloads data from nccp
'''

def downloadNCCPData():
    #download the data from ftp server
    print "Downloading data recursively from NCCP server using wget"
    print "Download URL: "+NCCP_SERVER_URL
    print "Storing wget log to "+WGET_LOG_FILE
    call(["wget", "-A",WGET_FILE_PATTERN,"-o",WGET_LOG_FILE,"-m",NCCP_SERVER_URL])
    print "Download complete!"


def createDB():
    conn = lite.connect(DB_LOCATION)
    c = conn.cursor()
    sql = 'CREATE TABLE IF NOT EXISTS ' + TABLE_NAME + ' (id INTEGER PRIMARY KEY AUTOINCREMENT, pid TEXT UNIQUE, format_id TEXT,file_name TEXT, md5_hash TEXT, date_created DATETIME)'
    c.execute(sql)


def uploadData(data_folder,file_pattern):
    conn = lite.connect(DB_LOCATION)
    conn.row_factory = lite.Row
    c = conn.cursor()
    for root,dirs,files in os.walk(data_folder):
        for f in files:
            if f.endswith('.'+file_pattern):
                client = d1_client.mnclient.MemberNodeClient(MN_BASE_URL,cert_path=CERTIFICATE_FOR_CREATE,key_path=CERTIFICATE_FOR_CREATE_KEY)
                filepath = os.path.join(root,f)
                metafilepath = os.path.join(META_OUTFILE_DIR,f.split('.')[0]+'.'+METAFILE_EXT)
                md5_hash = hashlib.md5(open(filepath, 'rb').read()).hexdigest()
                pid = NCCP_FILE_IDENTIFIER_PREFIX+f
                pid_meta = NCCP_FILE_IDENTIFIER_PREFIX+os.path.basename(metafilepath)
                pid_package = NCCP_FILE_IDENTIFIER_PREFIX+f.split('.')[0]+'_resourcemap.xml'
                c.execute('SELECT * FROM '+TABLE_NAME+' WHERE pid=?', (pid,))

                rows=c.fetchall()
                if len(rows)>0:
                    #c.execute('SELECT * FROM '+TABLE_NAME+' WHERE pid=?', (pid,))

                    for row in rows:
                        md5_hash_prev = row['md5_hash']
                        pid_prev = row['pid']
                        id_prev = row['id']
                        #print('{0}'.format(row['md5_hash']))
                    if md5_hash==md5_hash_prev:
                        print "already exists. skipping"
                        continue
                    else:
                        re_upload=True
                        #need to delete the file from gmn here
                        print "file changed. re-uploading"
                        client.delete(pid_prev)
                        c.execute('DELETE FROM '+TABLE_NAME+' WHERE pid=?', (pid,))
                print "Creating science object for file "+filepath
                print ""
                create_science_object_on_member_node(client,pid,filepath,SYSMETA_FORMATID)
                print "Creating science meta object for file "+metafilepath
                create_science_object_on_member_node(client,pid_meta,metafilepath,SYSMETA_FORMATID_METADATA)
                print "Creating resurce map with id "+pid_package+" for science object and metadata "
                create_package_on_member_node(pid_package, pid_meta, pid)
                # Insert a row of data
                #file_name="Rockland_Met_OneMin_2014_03_8370_49842.csv"
                #file_loc = "/home/mdmoinulh/"+file_name
                #example = {"pid":"NRDC:NCCP:Rockland_Met_OneMin_2014_03_8370_49842.csv","format_id":"text/csv","md5_hash":hashlib.md5(file_loc)}
                c = conn.cursor()
                data_to_save = (pid,SYSMETA_FORMATID,f,md5_hash,datetime.datetime.now())
                c.execute("INSERT INTO "+TABLE_NAME+"(pid,format_id,file_name,md5_hash,date_created) VALUES (?,?,?,?,?)",data_to_save)
                # Save (commit) the changes
                conn.commit()
                #print "sleeping for 10 seconds"
                #time.sleep(10)
    conn.close()

def create_resource_map_for_pids(package_pid, metadata_pid,data_pids):
  # Create a resource map generator that will generate resource maps that, by
  # default, use the DataONE production environment for resolving the object
  # URIs. To use the resource map generator in a test environment, pass the base
  # url to the root CN in that environment in the dataone_root parameter.
  resource_map_generator = d1_client.data_package.ResourceMapGenerator(dataone_root=CN_ROOT_URL)
  #print data_pids
  return resource_map_generator.simple_generate_resource_map(package_pid,
                                                             metadata_pid, data_pids)


def create_package_on_member_node(package_pid, metadata_file_pid, data_file_pid):
    client = d1_client.mnclient.MemberNodeClient(MN_BASE_URL,cert_path=CERTIFICATE_FOR_CREATE,key_path=CERTIFICATE_FOR_CREATE_KEY)
    #package_pid = NCCP_FILE_IDENTIFIER_PREFIX+metadata_file.split('.')[0]
    pids = []
    pids.append(data_file_pid)
    resource_map = create_resource_map_for_pids(package_pid, metadata_file_pid,pids)
    sys_meta = generate_system_metadata_for_science_object(package_pid,
    RESOURCE_MAP_FORMAT_ID, resource_map)
    client.create(package_pid, StringIO.StringIO(resource_map), sys_meta)



if __name__ == "__main__":
    #client = d1_client.mnclient.MemberNodeClient(MN_BASE_URL,cert_path=CERTIFICATE_FOR_CREATE,key_path=CERTIFICATE_FOR_CREATE_KEY)
    #print "Downloading files"
    #downloadNCCPData()
    #create metadata file
    createDB()
    print "Creating metadata files in directory "+META_OUTFILE_DIR
    call(['java', '-jar',JAR_FILE_LOC,'-outdir',META_OUTFILE_DIR,'-indir',SCIENCE_OBJECTS_DIR_PATH,'-lines',str(NUMLINES),'-infileext',INFILE_EXT])
    print "Uploading data and metadata files"
    uploadData(SCIENCE_OBJECTS_DIR_PATH,"csv")
