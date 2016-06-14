# toxxmlrpc

python library for executing xmlrpc over tox (toxcore)

Uses Toxpthon to establish a connection through the Tox network.

Usage is libxmlrpc like.

#Project Page

https://github.com/merlink01/toxxmlrpc

#Dependencies

-Toxcore https://github.com/irungentoo/toxcore

-Toxpython https://github.com/yodakohl/toxpython

-Setuptools

#Installation

sudo  python setup.py install

#Usage 

```python
Create Server:

PASSWORD = '123456'

import time
import toxxmlrpc

class object_to_serve:
    def ping(self,*args):
        return 'pong'

server = toxxmlrpc.Toxxmlrpc_Server(object_to_serve(), './tox_xmlrpc_server', PASSWORD, disable_auto_login=False)
serveraddress = server.client.get_address()
server.start()
print 'Server started with Pubkey: %s'%serveraddress


Create Client:

client = toxxmlrpc.Toxxmlrpc_Client( './tox_xmlrpc_client', PASSWORD, serveraddress, disable_auto_login=True)
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
```
More Informations could be found in the examples.


#Report Bugs

https://github.com/merlink01/toxxmlrpc/issues/new
