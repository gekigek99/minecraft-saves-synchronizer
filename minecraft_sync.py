import os
import paramiko
import time
import sys
from zipfile import ZipFile
from shutil import rmtree
import getpass
import subprocess
import threading

HOSTNAME = ''   #set the hostname of the server
USERNAME = ''   #set the username
PASSWORD = ''   #set password

MINECRAFT_APPDATA_FOLDER = 'C:\\Users\\username\AppData\Roaming\.minecraft\\'           #do not modify
SAVESFOLDER =       'C:\\Users\\username\AppData\Roaming\.minecraft\saves\\'            #do not modify
LOCALPATHZIP =      'C:\\Users\\username\AppData\Roaming\.minecraft\saves.zip'          #do not modify
LOCALPATH_DATE =    'C:\\Users\\username\AppData\Roaming\.minecraft\saves_date.txt'     #do not modify
REMOTEPATHZIP =     '/folderpath/in/server/saves_remote.zip'                            #add folder path on server (the file name is saves_date.txt)
REMOTEPATH_DATE =   '/folderpath/in/server/saves_remote_date.txt'                       #add folder path on server (the file name is saves_remote_date.txt)


def main_start():
    global HOSTNAME, USERNAME, PASSWORD, MINECRAFT_APPDATA_FOLDER, SAVESFOLDER, LOCALPATHZIP, LOCALPATH_DATE, REMOTEPATHZIP, REMOTEPATH_DATE, minecraft_exe_location, sftp
    user = getpass.getuser()
    SAVESFOLDER = SAVESFOLDER.replace("username", user)
    LOCALPATHZIP = LOCALPATHZIP.replace("username", user)
    LOCALPATH_DATE = LOCALPATH_DATE.replace("username", user)

    try:
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())   #non safe
            ssh.connect(HOSTNAME, 22, USERNAME, PASSWORD, timeout = 10800)
            print('ssh connected')
            sftp = ssh.open_sftp()
            print('sftp opened')
        except:
            answer = input('an error occurred while connecting to the server and it was impossible to syncronize, would you like to play offline anyway (y/N) (!!!use only in case this was the last pc you played on!!!)?')
            if answer == 'y' or answer == 'Y': 
                pass
            else:
                os.system('pause')
                sys.exit(0)

        choice = check()

        if choice == 1 or choice == 3:  #download local world and local_date
            print('downloading local world and local_date')
            downloader()

            print('removing old saves folder...')
            rmtree(SAVESFOLDER)
            os.mkdir(SAVESFOLDER)       #rmtree(SAVESFOLDER) remove the folder

            fileunzipper()

        try:
            sftp.close()
            print('sftp closed')
            ssh.close()
            print('ssh disconnected')
        except Exception as e:
            print (e, "unable to close connection (maybe i wasn' t connected at all?")
            os.system('pause')
            sys.exit(0)

    except Exception as e:
        print(e)
        os.system('pause')
        sys.exit(0)


def main_stop():
    global HOSTNAME, USERNAME, PASSWORD, MINECRAFT_APPDATA_FOLDER, SAVESFOLDER, LOCALPATHZIP, LOCALPATH_DATE, REMOTEPATHZIP, REMOTEPATH_DATE, minecraft_exe_location, sftp
    user = getpass.getuser()
    SAVESFOLDER = SAVESFOLDER.replace("username", user)
    LOCALPATHZIP = LOCALPATHZIP.replace("username", user)
    LOCALPATH_DATE = LOCALPATH_DATE.replace("username", user)

    try:
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())   #non safe
            ssh.connect(HOSTNAME, 22, USERNAME, PASSWORD, timeout = 10800)
            print('ssh connected')
            sftp = ssh.open_sftp()
            print('sftp opened')
        except:
            print('an error occurred while connecting to the server and it was impossible to syncronize')
            os.system('pause')
            sys.exit(0)

        choice = check()

        if choice == 0 or choice == 2 or choice == 4:  #upload local world and local_date
            filezipper()

            print('uploading local world and local_date')
            uploader()

        try:
            sftp.close()
            print('sftp closed')
            ssh.close()
            print('ssh disconnected')
        except Exception as e:
            print (e, "unable to close connection (maybe i wasn' t connected at all?")
            os.system('pause')
            sys.exit(0)

        print("If minecraft closed abruptly you can still backup your saves by going to folder:", SAVESFOLDER)

    except Exception as e:
        print(e)
        os.system('pause')
        sys.exit(0)



def check():
    localpath_file_exist = os.path.isfile(LOCALPATH_DATE)
    remotepath_file_exist = remotepath_file_exist_checker()
    print('localpath_file_exist: ' + str(localpath_file_exist))
    print('remotepath_file_exist: ' + str(remotepath_file_exist))
    
    if localpath_file_exist and remotepath_file_exist:
        with open(LOCALPATH_DATE,'r') as f:
            localdate = float(f.read())
        with sftp.open(REMOTEPATH_DATE, 'r') as f_rem:
            remotedate = float(f_rem.read())
        
        if localdate > remotedate:                
            return 0    #upload local world and local_date
        elif localdate < remotedate:
            return 1    #download remote world and remote_date
        else:
            print('the REMOTEPATH_DATE files are identical!')

    elif localpath_file_exist and not remotepath_file_exist:
        return 2        #upload local world and local world_date

    elif not localpath_file_exist and remotepath_file_exist:
        return 3        #download remote world and remote world_date

    else:
        print('first launch eh boy?!?!')
        return 4        #upload local world and local world_date


def remotepath_file_exist_checker():
    try:
        sftp.stat(REMOTEPATH_DATE)
    except IOError as e:
        if e.errno == 2:
            return False
    else:
        return True



def retrieve_file_paths(dirName):       #Declare the function to return all file paths of the particular directory
  filePaths = []        #setup file paths variable
   
  for root, directories, files in os.walk(dirName): #Read all directory, subdirectories and file lists
    for filename in files:
        filePath = os.path.join(root, filename)     #Create the full filepath by using os module.
        filePaths.append(filePath)
        
  return filePaths      #return all paths



def filezipper():
    filePaths = retrieve_file_paths(LOCALPATHZIP[:-4])
    print('The following files will be zipped: ', end = '')
    #for fileName in filePaths:
    #    print(fileName)
    print(str(len(filePaths)) + ' files')
    
    zip_file = ZipFile(LOCALPATHZIP, 'w')
    with zip_file:
        for file in filePaths:  #writing each file one by one
            zip_file.write(file, os.path.relpath(file, LOCALPATHZIP[:-4])) #LOCALPATH is used to set a root directory and avoid the creation of a zip file with file names starting from C:\\...
    print('new LOCALPATHZIP file was created successfully!')


def fileunzipper():
    print('extracting LOCALPATHZIP to saves folder...')
    with ZipFile(LOCALPATHZIP, 'r') as zip_f:
        zip_f.extractall(SAVESFOLDER)
    print('done')


def uploadinfo_thread():
    try:
        ssh_thread = paramiko.SSHClient()
        ssh_thread.set_missing_host_key_policy(paramiko.AutoAddPolicy())   #non safe
        ssh_thread.connect(HOSTNAME, 22, USERNAME, PASSWORD, timeout = 10800)
        sftp_thread = ssh_thread.open_sftp()

        remotesize = 0
        counter_avg = 0
        data_transfered_last_second_avg = 0
        localsize = os.path.getsize(LOCALPATHZIP)
        while remotesize < localsize:
            last_remotesize = remotesize
            remotesize = sftp_thread.stat(REMOTEPATHZIP).st_size
            
            percentage = round((remotesize/localsize)*100, 2)
            data_transfered_last_second = remotesize - last_remotesize
            data_transfered_last_second_avg = ((data_transfered_last_second_avg * counter_avg) + data_transfered_last_second) / (counter_avg + 1)
            time_remaining_sec = (localsize - remotesize) / data_transfered_last_second_avg
            ETA = (str(int(time_remaining_sec//60)) + 'm:' + str(int(time_remaining_sec%60))+ 's')
            print(str(percentage) + '%' + '\t' + str(int(data_transfered_last_second/1024)) + 'KB/s  ' + '\t' + 'uploading LOCALPATHZIP --> REMOTEPATHZIP' + '\tETA: ' + ETA + '\tdata transfered: ' + str(int(remotesize/1024)) + '/' + str(int(localsize/1024)) + ' KB', end = "\r")
            counter_avg += 1
            time.sleep(1)
        print(' ' * 200, end = "\r")
        print(str(percentage) + '%\tdone' + '\tdata transfered: ' + str(int(localsize/1024)) + '/' + str(int(remotesize/1024)) + ' KB')

    except Exception as e:
        print('exception in uploadinfo_thread', e)
        sys.exit(0)
    
    try:
        sftp_thread.close()
        ssh_thread.close()
    except Exception as e:
        print(e)
        pass


def uploader():
    uploadinfo = threading.Thread(target = uploadinfo_thread, args = ())
    uploadinfo.start()
    sftp.put(LOCALPATHZIP, REMOTEPATHZIP, callback=None, confirm=True)
    uploadinfo.join()
    print('upload of LOCALPATHZIP was successful!')
    print('uploading LOCALPATH_DATE --> REMOTEPATH_DATE...')
    sftp.put(LOCALPATH_DATE, REMOTEPATH_DATE, callback=None, confirm=True)
    print('upload of LOCALPATH_DATE was successful!')

def downloadinfo_thread():
    try:
        ssh_thread = paramiko.SSHClient()
        ssh_thread.set_missing_host_key_policy(paramiko.AutoAddPolicy())    #non safe
        ssh_thread.connect(HOSTNAME, 22, USERNAME, PASSWORD, timeout = 10800)
        sftp_thread = ssh_thread.open_sftp()

        localsize = 0
        counter_avg = 0
        data_transfered_last_second_avg = 0
        remotesize = sftp_thread.stat(REMOTEPATHZIP).st_size
        while localsize < remotesize:
            last_localsize = localsize
            localsize = os.path.getsize(LOCALPATHZIP)
            
            percentage = round((localsize/remotesize)*100, 2)
            data_transfered_last_second = localsize - last_localsize
            data_transfered_last_second_avg = ((data_transfered_last_second_avg * counter_avg) + data_transfered_last_second) / (counter_avg + 1)
            time_remaining_sec = (remotesize - localsize) / data_transfered_last_second
            ETA = (str(int(time_remaining_sec//60)) + 'm:' + str(int(time_remaining_sec%60))+ 's')
            print(str(percentage) + '%' + '\t' + str(int(data_transfered_last_second/1024)) + 'KB/s  ' + '\t' + 'downloading REMOTEPATHZIP --> LOCALPATHZIP' + '\tETA: ' + ETA + '\tdata transfered: ' + str(int(localsize/1024)) + '/' + str(int(remotesize/1024)) + ' KB', end = "\r")
            counter_avg += 1
            time.sleep(1)
        print(' ' * 200, end = "\r")
        print(str(percentage) + '%\tdone' + '\tdata transfered: ' + str(int(localsize/1024)) + '/' + str(int(remotesize/1024)) + ' KB')
        
    except Exception as e:
        print('exception in downloadinfo_thread', e)
        sys.exit(0)
    
    try:
        sftp_thread.close()
        ssh_thread.close()
    except Exception as e:
        print(e)
        pass


def downloader():
    downloadinfo = threading.Thread(target = downloadinfo_thread, args = ())
    downloadinfo.start()
    sftp.get(REMOTEPATHZIP, LOCALPATHZIP, callback=None)
    downloadinfo.join()
    print('download of REMOTEPATHZIP was successful!')
    print('downloading REMOTEPATH_DATE --> LOCALPATH_DATE...')
    sftp.get(REMOTEPATH_DATE, LOCALPATH_DATE, callback=None)
    print('download of REMOTEPATH_DATE was successful!')


def minecraft_exe_finder():
    global MINECRAFT_APPDATA_FOLDER, minecraft_exe_location
    
    MINECRAFT_APPDATA_FOLDER = MINECRAFT_APPDATA_FOLDER.replace("username", getpass.getuser())
    if not os.path.isfile(MINECRAFT_APPDATA_FOLDER + 'minecraft_exe_location.txt'):
        with open (MINECRAFT_APPDATA_FOLDER + 'minecraft_exe_location.txt', 'w') as f:
            minecraft_exe_location = input('path to minecraft launcher executable:')
            f.write(minecraft_exe_location)
    else:
        print('i already know where minecraft exe is')
        with open (MINECRAFT_APPDATA_FOLDER + 'minecraft_exe_location.txt', 'r') as f:
            minecraft_exe_location = f.read()


def localpath_date_updater():
    with open(LOCALPATH_DATE, 'w') as f:
        f.write(str(time.time()))

    print('new LOCALPATH_DATE file was created successfully!')

        
if __name__ == '__main__':
    minecraft_exe_finder()
    
    main_start()
    try:
        p = subprocess.Popen(minecraft_exe_location)
        print('--------------------MINECRAFT IS PLAYING--------------------')
        p.wait()
        print('--------------------MINECRAFT TERMINATED--------------------')
    except Exception as e:
        print(e)
        print('a problem was encountered while trying to open minecraft')
        os.system('pause')
        sys.exit(0)
    finally:
        localpath_date_updater()
        main_stop()
        os.system('pause')
        sys.exit(0)
