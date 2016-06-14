from ctypes import *
import sys
import threading
import time
import os
import os.path
import traceback
import Queue
import logging
import base64

logger = logging.getLogger('Toxclient')




from toxpython import Tox
from toxpython import TOX_USER_STATUS_NONE
from toxpython import TOX_MESSAGE_TYPE_NORMAL



class Toxclient(Tox,threading.Thread):

    running = False

    def __init__(self,configfolder,password=None,name=None,workingdir=None):
        """If no Password given, Auto Login is disabled"""
        
        if not workingdir:
            workingdir = os.path.expanduser('~/.config/toxxmlrpc/')
            
        if not os.path.isdir(workingdir):
            os.makedirs(workingdir)
        os.chdir(workingdir)
        sys.path.append(workingdir)

        logger.info('Workingdir: %s'%os.getcwd())
        
        threading.Thread.__init__(self)
        self.queue_recv_lock = threading.Lock()
        self.data_send_lock = threading.Lock()
        self.queue_recv = []
        self.status = 'offline'

        self.password = password
        self.configfolder = configfolder
        if not os.path.isdir(self.configfolder):
            os.mkdir(self.configfolder)
            
        logger.info('Version: %s.%s.%s'%(self.version_major(),self.version_minor(),self.version_patch()))

        logger.info("Using configpath: " + str(self.configfolder))

        self.savepath = self.configfolder + '/privatekey'

        self.init(self.savepath)
        if name:
            logger.debug('Name: %s'%name)
            self.setName(name)
        logger.debug('Address: %s'%self.get_address())


        self.save(self.savepath)
        self.set_status(TOX_USER_STATUS_NONE)

        self.bootstrap("195.154.119.113",33445,"E398A69646B8CEACA9F0B84F553726C1C49270558C57DF5F3C368F05A7D71354")
        if(self.self_get_connection_status() == False):
            self.status = 'offline'
            logger.info('Offline')
        else:
            self.status = 'online'
            logger.info('Online')

    def get_friend_list_extended(self):
        friend_list = {}
        
        for f in self.get_friend_list():
            friend_list[f] = {}
            friend_list[f]['pubkey'] = self.friend_get_public_key(f)
            friend_list[f]['name'] = self.friend_get_name(f)
            friend_list[f]['status'] =  self.friend_get_status(f)
            friend_list[f]['connected'] =  self.friend_get_connection_status(f)
        return friend_list
            
    def friend_add_without_request(self, public_key):
        return self.friend_add_norequest(public_key) 

    def friend_add_with_request(self, public_key, message):
        if (self.friend_add(public_key, message) == True):
            logger.info("Adding friend successful: " + public_key)
        else:
            logger.info("Adding friend failed")
        self.save(self.savepath)

    def on_friend_request(self,public_key, message):
        logger.info('Connection Request: %s %s'%(public_key,message))
        if self.password:
            if message == self.password:
                self.friend_add_norequest(public_key)
                self.save(self.savepath)
                logger.info('Accepted')
            else:
                logger.info('Wrong Password')
        else:
            logger.info('Connection Forbidden')


    def on_connection_status(self,connection_status):
        if(self.self_get_connection_status() == True):
            self.queue_recv_lock.acquire()
            self.queue_recv = []
            self.queue_recv_lock.release()
            self.status = 'online'
            logger.info('Online')
        else:
            self.status = 'offline'
            logger.info('Offline')
            time.sleep(1)
            if(self.self_get_connection_status() == False):
                self.status = 'offline'
                logger.info('Offline')
                self.bootstrap("195.154.119.113",33445,"E398A69646B8CEACA9F0B84F553726C1C49270558C57DF5F3C368F05A7D71354")

    def on_friend_message(self,friend_id, message_type, message):
        logger.info(self.friend_get_name(friend_id) + ": " + message)
        self.friend_send_lossless_packet(friend_id,'a')

    def run(self):
        self.running = True
        while(self.running):
            self.iterate()
            time.sleep(self.sleepInterval()/1000.0)
        self.kill()

    def stop(self):
        self.running = False
        pass

    def data_send(self,friendId,data,timeout=10):

        message_type = 180

        max_block_size = 1371

        self.data_send_lock.acquire()

        blockid = 0
        offset = 0
        size = len(data)
        while 1:
            block = '%s' % blockid
            
            while not self.friend_get_connection_status(friendId):
                logger.debug('wait for connection')
                time.sleep(1)

            block += (data[offset:offset + max_block_size])
            offset += max_block_size

            ret = False
            time_to_wait = int(time.time()) + timeout
            while ret == False:
                timenow = int(time.time())
                if timenow > time_to_wait:
                    logger.warning('Raising Error, Timeout reached')
                    self.data_send_lock.release()
                    return False
                
                ret = self.friend_send_lossless_packet_simple(friendId,message_type,block)
                if ret == False:
                    time.sleep(0.1)

            if blockid == 2:
                break

            if offset >= len(data):
                blockid = 2
            else:
                blockid = 1

        self.data_send_lock.release()
        return True


    def data_recv(self):
        self.queue_recv_lock.acquire()
        for entry in self.queue_recv:
            if entry['done']:
                self.queue_recv.remove(entry)
                self.queue_recv_lock.release()
                return entry
        self.queue_recv_lock.release()
        return None

    def friend_send_lossless_packet_simple(self,friendId,message_type,message):
        assert 159 < message_type < 191
        assert len(message) < 1374, 'Got: %s'%len(message)

        logger.debug('Send Lossless: Friend:%s Type:%s Message:%s'%(friendId,message_type,len(message)))
        raw_bytes = (c_ubyte * len(message)).from_buffer_copy(message)
        ret = self.friend_send_lossless_packet(friendId,message_type,raw_bytes)
        if(ret == False):
            return False
        else:
            return True

    def on_friend_lossless_packet_callback(self,friendId,message_type,message):
        logger.debug('Got Lossless: Friend:%s Type:%s Message:%s'%(friendId,message_type,len(message)))
        
        self.queue_recv_lock.acquire()
        block_number = int(message[:1])
        
        job_exists = False
        for entry in self.queue_recv:
            if entry['friendId'] == friendId:
                job_exists = True
        
        if block_number == 0:
            self.queue_recv.append({'data':message[1:],'done':False,'message_type':message_type,'friendId':friendId})
        elif block_number == 1:
            if job_exists:
                self.queue_recv[-1]['data'] += message[1:]
            else:
                logger.info('Got Bad Fragment')
        elif block_number == 2:
            if job_exists:
                self.queue_recv[-1]['done'] = True
                if message_type == 181:
                    self.queue_recv[-1]['data'] = base64.b64decode(self.queue_recv[-1]['data'])
            else:
                logger.info('Got Bad Fragment')
        else:
            self.queue_recv_lock.release()
            logger.info('Got Unknown Fragment')
            raise IOError

        self.queue_recv_lock.release()


    def on_friend_connection_status(self,friendId, connection_status):
        if connection_status == False:
            self.queue_recv_lock.acquire()
            for entry in self.queue_recv:
                if entry['friendId'] == friendId:
                    logger.info('Cleanup Incomplete Recieve Data of Friend: %s'%friendId)
                    self.queue_recv.remove(entry)
            self.queue_recv_lock.release()
            


