import toxclient
import time
import xmlrpclib
import sys
import threading
import logging
import StringIO
import traceback

from xmlrpclib import Fault
logger = logging.getLogger('Toxxmlrpc_Server')


class Toxxmlrpc_Server(threading.Thread):
    def __init__(self, srv_obj, path, password=None, client_id=None, disable_auto_login=True):
        """Toxxmlrpc_Server:
        
        srv_obj: Python Object to Serve
        
        path: Settingsfolder
        
        password: You need a password for auto connecting Clients
        
        client_id: Server connects to one pre defined Client,
                Nessessary if you want to build a Monitoring solution f.e.
                If None: Client connects to Server like normal
        """
        
        threading.Thread.__init__(self)
        if disable_auto_login:
            self.client = toxclient.Toxclient(path)
        else:
            self.client = toxclient.Toxclient(path,password)
        self.password = password
        self.client_id = client_id
        self.srv_obj = srv_obj
        

    def run(self):
        self.client.start()
        while self.client.status == 'offline':
            time.sleep(1)

        self.running = True
        oldstat = 'offline'
        while(self.running):

            if oldstat != self.client.status:
                logger.info('XMLRPC: %s'%self.client.status)
                oldstat = self.client.status
                if self.client_id:
                    already_added = False
                    for f in self.client.get_friend_list():
                        if self.client.friend_get_public_key(f) in self.client_id:
                            already_added = True
                            break
                    if not already_added:
                        self.client.friend_add_with_request(self.client_id,self.password)
            while self.client.status == 'online' and self.running:
                rec = self.client.data_recv()
                if rec:
                    data = rec['data']

                    try:
                        params, method = xmlrpclib.loads(data,use_datetime=True)
                        logger.info('Client[%s] Executing: %s%s'%(rec['friendId'],method,repr(params)))
                        if method is not None:
                            method = getattr(self.srv_obj,method)
                            response = method(*params)

                        else:
                            raise IOError, 'No Command given'
                        response = (response,)
                        response = xmlrpclib.dumps(response, methodresponse=1, allow_none=True)
                    except Fault, fault:
                        print 'Exception %s'%fault
                        response = xmlrpclib.dumps(fault, allow_none=True,
                                                   encoding='utf-8')
                    except:
                        # report exception back to server
                        exc_type, exc_value, exc_tb = sys.exc_info()
                        print 'Exception %s : %s'%(exc_type, exc_value)
                        response = xmlrpclib.dumps(
                            xmlrpclib.Fault(1, "%s:%s" % (exc_type, exc_value)),
                            encoding='utf-8', allow_none=True,
                            )
                    self.client.data_send(rec['friendId'],response)
                time.sleep(0.01)
            time.sleep(1)
        self.client.stop()

    def stop(self):
        self.running = False


