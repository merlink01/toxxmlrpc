import os
import sys
import logging
logger = logging.getLogger('Toxlibautoinstall')

workingdir = os.path.expanduser('~/.config/toxlib/')
if not os.path.isdir(workingdir):
    os.makedirs(workingdir)
os.chdir(workingdir)
sys.path.append(workingdir)


counter = 0
while 1:
    counter += 1
    if counter > 5:
        raise IOError, 'Auto Instalation not possible'
    try:
        import toxpython
        break
    except ImportError:
        if 'No module named toxpython' in sys.exc_info()[1]:
            logger.info('Installing toxpython library...')
            import StringIO
            import zipfile
            import urllib2
            #~ url = "https://github.com/yodakohl/toxpython/archive/master.zip"
            url = "https://github.com/merlink01/toxpython/archive/master.zip"
            webfile = urllib2.urlopen(url)
            webfileIO = StringIO.StringIO(webfile.read())
            ziphandle = zipfile.ZipFile(webfileIO)
            path = 'toxpython-master/toxpython/'
            if not os.path.isdir('%s/%s'%(workingdir,'toxpython/')):
                os.makedirs('%s/%s'%(workingdir,'toxpython/'))
                
            for name in ziphandle.namelist():
                if path in name:
                    if not name.endswith('/'):
                        outfile = open(os.path.join('%s/%s'%(workingdir,'toxpython/'), os.path.basename(name)), 'wb')
                        outfile.write(ziphandle.read(name))
                        outfile.close()
            logger.info('Done')
            
        if 'libtox not found.' in sys.exc_info()[1]:
            logger.info('Tox Library not found.')
            import platform
            import StringIO
            import zipfile
            import urllib2
            
            system = platform.system()
            logger.info('Try Autoinstallation on System: %s'%system)
            if system == 'Windows':
                logger.info('Try Autoinstallation on System: %s'%system)
                url = "https://build.tox.chat/view/libtoxcore/job/libtoxcore_build_windows_x86_shared_release/lastSuccessfulBuild/artifact/libtoxcore_build_windows_x86_shared_release.zip"
                webfile = urllib2.urlopen(url)
                webfileIO = StringIO.StringIO(webfile.read())
                ziphandle = zipfile.ZipFile(webfileIO)
                outfile = open(os.path.join(workingdir, 'libtox.dll'), 'wb')
                outfile.write(ziphandle.read('bin/libtox.dll'))
                outfile.close()
                logger.info('Done')
            else:
                raise IOError, 'Autoinstallation not implemented for your system: %s\nPlease install "toxcore"'%system


    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise IOError, 'Cant get toxpython to work'

logger.info('Toxlib loaded successfull...')
