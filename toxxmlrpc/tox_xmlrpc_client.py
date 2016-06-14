import toxclient
import threading
import xmlrpclib
import time
import sys
import logging
logger = logging.getLogger('Toxxmlrpc_Client')

class _Method:
    # some magic to bind an XML-RPC method to an RPC server.
    # supports "nested" methods (e.g. examples.getStateName)
    def __init__(self, send, name):
        self.__send = send
        self.__name = name
    def __getattr__(self, name):
        return _Method(self.__send, "%s.%s" % (self.__name, name))
    def __call__(self, *args):
        return self.__send(self.__name, args)


class Toxxmlrpc_Client():
    def __init__(self,path,password=None,server_id=None, disable_auto_login=True,timeout=10):
        self.timeout = timeout
        self.server_id = server_id
        self.password = password
        self.disable_auto_login = disable_auto_login
        if disable_auto_login:
            self.client = toxclient.Toxclient(path)
        else:
            self.client = toxclient.Toxclient(path,password)
        self.exec_lock = threading.Lock()

    def start(self):
        self.client.start()
        #~ if not self.disable_auto_login:
            #~ while self.client.status == 'offline':
                #~ time.sleep(1)
            #~ logger.info('Client: %s'%self.client.status)
        if self.server_id:
            already_added = False
            for f in self.client.get_friend_list():
                if self.client.friend_get_public_key(f) in self.server_id:
                    already_added = True
                    logger.info('Server already in added')
                    break
            if not already_added:
                self.client.friend_add_with_request(self.server_id,self.password)
                logger.info('Started Friend request to Server')
        else:
            logger.info('No Server ID given')


    def stop(self):
        self.client.stop()

    def __request(self,methodname,args):
        data = xmlrpclib.dumps(args,methodname)

        self.exec_lock.acquire()
        if not self.client.data_send(0,data,self.timeout):
            logger.warning('Raising Error, Timeout reached')
            self.exec_lock.release()
            raise IOError, 'Timeout'
        recdata = None

        time_to_wait = int(time.time()) + self.timeout
        while not recdata:
            timenow = int(time.time())
            if timenow > time_to_wait:
                logger.warning('Raising Error, Timeout reached')
                self.exec_lock.release()
                raise IOError, 'Timeout'
            recdata = self.client.data_recv()
            time.sleep(0.1)
        self.exec_lock.release()

        returndata = xmlrpclib.loads(recdata['data'])
        return returndata[0][0]

    def __getattr__(self, name):
        # magic method dispatcher
        return _Method(self.__request, name)

if __name__ == '__main__':
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    fmt_string = "[%(levelname)-7s]%(asctime)s.%(msecs)-3d %(name)s Thread:%(thread)s/%(module)s[%(lineno)-3d]/%(funcName)-10s  %(message)-8s "
    formatter = logging.Formatter(fmt_string)
    ch.setFormatter(formatter)
    root.addHandler(ch)
    t = Toxxmlrpc_Client('./tox_xmlrpc_client','123456','1CFE9A98D6FF924D569732A93F32FC2787F78676931ED77259E586DFABFDB67190C2926CE00A')
    t.start()
    try:
        print t.ping()
    except:
        print 'error'
    t.stop()
