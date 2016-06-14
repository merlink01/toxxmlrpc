import logging
import sys
import time

root = logging.getLogger()
root.setLevel(logging.WARNING)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
fmt_string = "[%(levelname)-7s]%(asctime)s.%(msecs)-3d %(name)s Thread:%(thread)s/%(module)s[%(lineno)-3d]/%(funcName)-10s  %(message)-8s "
formatter = logging.Formatter(fmt_string)
ch.setFormatter(formatter)
root.addHandler(ch)

import toxxmlrpc

PASSWORD = '123456'

class test:
    def listMethods(self):
        methlist = []
        for method in dir(self):
            if callable(getattr(self, method)):
                methlist.append(method)
        return methlist
        
    def ping(self,*args):
        return 'pong'
        
    def broken(self):
        raise IOError, 'This is a test exception'

print '#'*40
print 'Forward auto login Client --> Server'
print '#'*40
server = toxxmlrpc.Toxxmlrpc_Server(test(), './tox_xmlrpc_server_forward', PASSWORD, disable_auto_login=False)
serveraddress = server.client.get_address()
server.start()
print 'Server started with Pubkey: %s'%serveraddress


client = toxxmlrpc.Toxxmlrpc_Client( './tox_xmlrpc_client_forward', PASSWORD, serveraddress, disable_auto_login=True)
clientaddress = client.client.get_address()
client.start()
print 'Client started with Pubkey: %s'%clientaddress
print ''

print 'Test Ping'
assert client.ping(True) == 'pong'
print 'All OK, got Pong'
print ''

client.stop()
server.stop()
time.sleep(5)
print '#'*40
print 'Reverse auto login Server --> Client'
print '#'*40
client = toxxmlrpc.Toxxmlrpc_Client( './tox_xmlrpc_client_reverse', PASSWORD, disable_auto_login=False)
clientaddress = client.client.get_address()
client.start()
print 'Client started with Pubkey: %s'%clientaddress
print ''


server = toxxmlrpc.Toxxmlrpc_Server(test(), './tox_xmlrpc_server_reverse', PASSWORD, clientaddress, disable_auto_login=True)
serveraddress = server.client.get_address()
server.start()
print 'Server started with Pubkey: %s'%serveraddress

print 'Test Ping'
assert client.ping(True) == 'pong'
print 'All OK, got Pong'
print ''

client.stop()
server.stop()
time.sleep(5)
print '#'*40
print 'Paranoid connection (Transfer Server Pubkey to Client and Reverse)'
print '#'*40
server = toxxmlrpc.Toxxmlrpc_Server(test(), './tox_xmlrpc_server_para', disable_auto_login=True)
serveraddress = server.client.get_address()
server.start()
print 'Server started with Pubkey: %s'%serveraddress


client = toxxmlrpc.Toxxmlrpc_Client( './tox_xmlrpc_client_para', disable_auto_login=True)
clientaddress = client.client.get_address()
client.start()
print 'Client started with Pubkey: %s'%clientaddress

server.client.friend_add_without_request(clientaddress)
client.client.friend_add_without_request(serveraddress)

print 'Test Ping'
assert client.ping(True) == 'pong'
print 'All OK, got Pong'
print ''

client.stop()
server.stop()
time.sleep(5)

print '#'*40
print 'Test XMLRPC'
print '#'*40
server = toxxmlrpc.Toxxmlrpc_Server(test(), './tox_xmlrpc_server_forward', PASSWORD, disable_auto_login=False)
serveraddress = server.client.get_address()
server.start()
print 'Server started with Pubkey: %s'%serveraddress


client = toxxmlrpc.Toxxmlrpc_Client( './tox_xmlrpc_client_forward', PASSWORD, serveraddress, disable_auto_login=True)
clientaddress = client.client.get_address()
client.start()
print 'Client started with Pubkey: %s'%clientaddress
print ''

print 'Test Ping'
assert client.ping(True) == 'pong'
print 'All OK, got Pong'
print ''

print 'Following methods are available:'
methods = client.listMethods()
for m in methods:
    print m
print ''

try:
    print 'Test not available method'
    client.ding()
except:
    print 'All OK, This function has to crash'
print ''

try:
    print 'Test broken method'
    client.broken()
except:
    print 'All OK, This function has to crash'
print ''

client.stop()
server.stop()













