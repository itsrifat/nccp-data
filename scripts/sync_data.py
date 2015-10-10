#!/usr/bin/env python

#sys
from subprocess import call
import os
import time
import datetime
import hashlib
import logging
import sys
import StringIO

#3rd party
import sqlite3 as lite
import pyxb

# dataone specific
import d1_common.types.generated.dataoneTypes as dataoneTypes
import d1_common.const
import d1_client.mnclient
import d1_client.data_package


'''
GLOBAL VARIABLES
'''
#local sqlite database specific
DB_LOCATION = "nrdc_dataone.db"
TABLE_NAME = 'file_upload_history'

## dataone specific
NCCP_FILE_IDENTIFIER_PREFIX = 'NRDC_NCCP'
DATAONE_OBJECT_TYPES = {'data':'SCIENCE_OBJECT','metadata':'SCIENCE_METADATA','package':'RESOURCE_MAP'}
DATAONE_OBJECT_TYPES_ESXTENSION = {'data':'csv','metadata':'xml','package':'xml'}
FORMAT_IDS = {'data':'text/csv','metadata':'http://www.isotc211.org/2005/gmd','package':'http://www.openarchives.org/ore/terms'}
SYSMETA_RIGHTSHOLDER = 'CN=CA for GMN Client Side Certificates,O=NRDC,C=US,DC=cilogon,DC=org'
# BaseURL for the Member Node. If the script is run on the same server as the Member Node, this can be localhost
MN_BASE_URL = 'https://localhost/mn'
#Root url for the co-ordinating node
CN_ROOT_URL = 'https://cn-stage.test.dataone.org/cn'
#certificates
CERTIFICATE_FOR_CREATE = '/var/local/dataone/certs/client/client_cert.pem'
CERTIFICATE_FOR_CREATE_KEY = '/var/local/dataone/certs/client/client_key_nopassword.pem'

## nrdc specific
SCIENCE_OBJECTS_DIR_PATH_REMOTE = '/mnt/nrdc-public-ftp/Aggregated Data/Walker Basin Climate'
SCIENCE_OBJECTS_DIR_PATH_LOCAL = 'nccp-data'
FILE_EXT = 'csv'
METAFILE_EXT = 'xml'
NCCP_DATA_INTERVAL_TYPES=['OneMin','TenMin']
DEFAULT_FILE_VERSION = 1
VERSION_DELIMITER = '::'
## metadata generation specific
JAR_FILE_LOC = 'iso19115-xml-gen.jar'
META_OUTFILE_DIR = 'metadata'
NUMLINES = 10

'''
Functions db spefic
'''

def createDB(conn):
    '''
    This function creates a sqlite database to keep track of which files are being uploaded to the member node.

    '''
    c = conn.cursor()
    sql = 'CREATE TABLE IF NOT EXISTS ' + TABLE_NAME + \
          ' (id INTEGER PRIMARY KEY AUTOINCREMENT, pid TEXT UNIQUE, pid_metadata TEXT UNIQUE,pid_package TEXT UNIQUE,' \
          ' file_loc TEXT,file_name TEXT UNIQUE, md5_hash TEXT,' \
          ' version integer DEFAULT 1, date_created DATETIME, date_modified DATETIME)'
    c.execute(sql)

def table_exists(conn,table_name):
    '''
    This function checks whether the database table for keeping track of files hsaa been created
    '''
    c = conn.cursor()
    sql = "SELECT name FROM sqlite_master WHERE type='table' AND name='%s';"%TABLE_NAME
    c.execute(sql)
    rows = c.fetchall()
    if len(rows)==1:
        return True
    else:
        return False

'''
Class representing an object
'''
class Object(object):
    """This class represents an object in gmn"""
    def __init__(self,id=-1,pid=None, pid_metadata=None,pid_package=None, format_id=None,file_loc=None,file_name=None,md5_hash=None,version=1,
                                            date_created=datetime.datetime.now(),date_modified=datetime.datetime.now()):
        self.id = id
        self.pid = pid
        self.pid_metadata = pid_metadata
        self.pid_package = pid_package
        #self.format_id = format_id
        self.file_loc = file_loc
        self.file_name = file_name
        self.md5_hash = md5_hash
        self.version = version
        self.date_created = date_created
        self.date_modified = date_modified

'''
Functions dataone specific
'''

def create_object_on_member_node(client, pid, file_path, formatId):
    with open(file_path, 'rb') as f:
        sci_obj = f.read()
    sys_meta = generate_system_metadata_for_object(pid, formatId, sci_obj)
    client.create(pid, StringIO.StringIO(sci_obj), sys_meta)

def update_object_on_member_node(client, pid, new_file_path,new_pid, formatId):
    with open(new_file_path, 'rb') as f:
        sci_obj = f.read()
    sys_meta = generate_system_metadata_for_object(new_pid, formatId, sci_obj)
    client.update(pid, StringIO.StringIO(sci_obj),new_pid, sys_meta)

def generate_system_metadata_for_object(pid, format_id, science_object):
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

def create_resource_map_for_pids(package_pid, metadata_pid, data_pids):
    # Create a resource map generator that will generate resource maps that, by
    # default, use the DataONE production environment for resolving the object
    # URIs. To use the resource map generator in a test environment, pass the base
    # url to the root CN in that environment in the dataone_root parameter.
    resource_map_generator = d1_client.data_package.ResourceMapGenerator(
        dataone_root=CN_ROOT_URL)
    # print data_pids
    return resource_map_generator.simple_generate_resource_map(package_pid,
                                                               metadata_pid, data_pids)


def create_package_on_member_node(client, package_pid, metadata_file_pid, data_file_pid):
    pids = []
    pids.append(data_file_pid)
    resource_map = create_resource_map_for_pids(package_pid, metadata_file_pid, pids)
    sys_meta = generate_system_metadata_for_object(package_pid,FORMAT_IDS['package'], resource_map)
    client.create(package_pid, StringIO.StringIO(resource_map), sys_meta)

def update_package_on_member_node(client, package_pid,package_pid_new, metadata_file_pid, data_file_pid):
    pids = []
    pids.append(data_file_pid)
    resource_map = create_resource_map_for_pids(package_pid, metadata_file_pid, pids)
    sys_meta = generate_system_metadata_for_object(package_pid_new,FORMAT_IDS['package'], resource_map)
    client.update(package_pid, StringIO.StringIO(resource_map),package_pid_new, sys_meta)


'''
Functions sync specific
'''

def copy_directory(remote_directory,local_directory):
    pass


def get_object(db_conn,file_name):
    c = db_conn.cursor()
    sql = "SELECT * from "+TABLE_NAME+" WHERE file_name='%s'"%file_name
    c.execute(sql)
    rows = c.fetchall()
    if not len(rows) > 0:
        return None
    for row in rows:
        obj = Object(id=row['id'], pid=row['pid'],pid_metadata=row['pid_metadata'],pid_package=row['pid_package'],
                            file_loc =row['file_loc'],file_name= row['file_name'], md5_hash=row['md5_hash'],
                            version=row['version'],date_created=row['date_created'],date_modified=row['date_modified'])
        return obj
    return None

def compare_file_in_gmn(obj_in_gmn,file_loc,file_name):
    file_path = os.path.join(file_loc, file_name)
    with open(file_path,'rb') as f:
        md5_hash = hashlib.md5(f.read()).hexdigest()
    if obj_in_gmn.md5_hash==md5_hash:
        return True
    else:
        return False

def generate_pid(db_conn,file_name,file_type):
    file_name_wihtout_extension = file_name.split('.')[0]
    obj = get_object(db_conn,file_name)
    pid_prefix = NCCP_FILE_IDENTIFIER_PREFIX+'_'+DATAONE_OBJECT_TYPES[file_type]
    if obj:
        curr_version = obj.version
        new_pid = pid_prefix + '_' + file_name_wihtout_extension + VERSION_DELIMITER + str(curr_version+1) + '.' +DATAONE_OBJECT_TYPES_ESXTENSION[file_type]
    else:
        new_pid = pid_prefix + '_' + file_name_wihtout_extension + VERSION_DELIMITER + str(DEFAULT_FILE_VERSION)+'.'+DATAONE_OBJECT_TYPES_ESXTENSION[file_type]
    return new_pid

def file_qualifies(file_path,expected_extension,expected_data_intervals):
    if file_path.endswith('.'+expected_extension):
        for interval in expected_data_intervals:
            if interval in file_path:
                return True
        return False
    else:
        return False

def save_to_db(db_conn,obj):
    data_to_save = (obj.pid, obj.pid_metadata,obj.pid_package, obj.file_loc, obj.file_name, obj.md5_hash,
                                                        obj.version,obj.date_created,obj.date_modified)
    c = db_conn.cursor()
    c.execute("INSERT INTO " + TABLE_NAME +
              "(pid,pid_metadata,pid_package,file_loc,file_name,md5_hash,version,date_created,date_modified) VALUES (?,?,?,?,?,?,?,?,?)", data_to_save)
    db_conn.commit()

def update_to_db(db_conn,obj):
    sql = "UPDATE "+TABLE_NAME+" SET pid=?,pid_metadata=?,pid_package=?, md5_hash=?, version=?, date_modified=? WHERE id=?"
    c = db_conn.cursor()
    c.execute(sql,(obj.pid,obj.pid_metadata,obj.pid_package, obj.md5_hash, obj.version, obj.date_modified,obj.id))
    print "Updated ", c.rowcount," object"
    db_conn.commit()

def sync_file(client,db_conn,file_loc,file_name):
    file_path = os.path.join(file_loc,file_name)
    metafile_name = file_name.split('.')[0] + '.' + METAFILE_EXT
    metafile_path = os.path.join(META_OUTFILE_DIR, metafile_name)
    obj_in_gmn = get_object(db_conn,file_name)
    #print 'already in server:', obj_in_gmn.file_name
    with open(file_path,'rb') as f:
        md5_hash = hashlib.md5(f.read()).hexdigest()
    if obj_in_gmn:
        print file_name, " exists in version "+str(obj_in_gmn.version)
        #now chekc to see if its the same file or the file is modified locally
        if not compare_file_in_gmn(obj_in_gmn,file_loc,file_name):
            # if modified update the modified version with incremented version number
            print "Files are different in gmn and local. Going ot be updated"
            new_pid = generate_pid(db_conn,file_name,'data')
            update_object_on_member_node(client, obj_in_gmn.pid, file_path,new_pid, FORMAT_IDS['data'])
            new_pid_metadata = generate_pid(db_conn,file_name,'metadata')
            #print 'new meetadata pid', new_pid_metadata
            update_object_on_member_node(client, obj_in_gmn.pid_metadata, metafile_path,new_pid_metadata, FORMAT_IDS['metadata'])
            new_pid_package = generate_pid(db_conn,file_name,'package')
            update_package_on_member_node(client, obj_in_gmn.pid_package,new_pid_package, new_pid_metadata, new_pid)

            new_obj_in_gmn = Object(id=obj_in_gmn.id,pid=new_pid,pid_metadata=new_pid_metadata,
                                pid_package=new_pid_package, md5_hash=md5_hash, version=obj_in_gmn.version+1,
                                date_modified=datetime.datetime.now())
            update_to_db(db_conn,new_obj_in_gmn)
        else:
            print "Files are identical"
        #Object already exists

    else:
        #its a new local object, insert it with version 1

        pid_data = generate_pid(db_conn,file_name,'data')
        pid_metadata = generate_pid(db_conn,file_name,'metadata')
        pid_package = generate_pid(db_conn,file_name,'package')

        metafile_path = os.path.join(META_OUTFILE_DIR,file_name.split('.')[0] + '.' + METAFILE_EXT)
        print "Creating science object for file " + file_path
        create_object_on_member_node(client, pid_data, file_path, FORMAT_IDS['data'])
        print "Creating science metadata object for file " + metafile_path
        create_object_on_member_node(client, pid_metadata, metafile_path, FORMAT_IDS['metadata'])
        #pid_package =
        create_package_on_member_node(client,pid_package, pid_metadata, pid_data)

        obj = Object(id=None,pid=pid_data,pid_metadata=pid_metadata,pid_package=pid_package,
                    file_loc=file_loc,file_name=file_name, md5_hash=md5_hash, version=1,
                    date_created=datetime.datetime.now(),date_modified=datetime.datetime.now())
        save_to_db(db_conn,obj)


def generate_medata_for_data_files(jar_file_loc, indir,outdir,num_lines,infile_ext):
    call(['java', '-jar', jar_file_loc, '-outdir', outdir, '-indir',
          indir, '-lines', str(num_lines), '-infileext', infile_ext])

def sync_data(client,db_conn,data_directory):
    for root, dirs, files in os.walk(data_directory):
        for f in files:
            file_path = os.path.join(root,f)
            if file_qualifies(file_path,FILE_EXT,NCCP_DATA_INTERVAL_TYPES):
                #sync the data file, metadata file and resource map
                sync_file(client,db_conn,root,f)
                #sync the science metadata file
                #metafile_name = f.split('.')[0] + '.' + METAFILE_EXT
                #sync_file(client,db_conn,META_OUTFILE_DIR,metafile_name)
            else:
                print file_path, "is skipped from syncing"



if __name__ == "__main__":
    #Create client and conn
    client = d1_client.mnclient.MemberNodeClient(MN_BASE_URL, cert_path=CERTIFICATE_FOR_CREATE,
                                                                key_path=CERTIFICATE_FOR_CREATE_KEY)
    conn = lite.connect(DB_LOCATION)
    conn.row_factory = lite.Row
    if not table_exists(conn,TABLE_NAME):
        print "Creating DATABASE table for the first time"
        createDB(conn)
    print "Copying all the files from the remote directory to local directory"
    copy_directory(SCIENCE_OBJECTS_DIR_PATH_REMOTE,SCIENCE_OBJECTS_DIR_PATH_LOCAL)
    print "Generating metadata for local directory"
    generate_medata_for_data_files(JAR_FILE_LOC, SCIENCE_OBJECTS_DIR_PATH_LOCAL, META_OUTFILE_DIR, NUMLINES,FILE_EXT)
    print "Syncing data in generic member node"
    sync_data(client,conn,SCIENCE_OBJECTS_DIR_PATH_LOCAL)
