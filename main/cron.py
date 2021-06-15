import kronos
from .models import Backup, BackupInstance, FSPath, FSStorage
import paramiko
import datetime
import pytz
from .lib import show_error, send_mail
import logging
import sys
from django.db import connection
from backup_management import env
import os
import shutil

logger = logging.getLogger('BACKUP-MANAGEMENT')
logging.basicConfig(stream=sys.stdout, level=logging.ERROR)

@kronos.register(env.CRONJOB)
def update_backup_instances_job():
    try:
        backups = Backup.objects.all()
        for i in backups:
            try:
                if i.storage_type == "fs" and i.fs_storage != None:
                    try:
                        server_ip = (str(i.fs_storage)).split(":")[0]
                        fs_storage = FSStorage.objects.filter(server_ip__exact=str(server_ip))[0]
                        ssh_private_key = fs_storage.ssh_private_key
                        ssh_user = fs_storage.ssh_user
                        connection.close()
                    except Exception as e:
                        show_error(e)
                    ssh = paramiko.SSHClient()
                    # Auto add host to known hosts
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    # Connect to server
                    try:
                        key = paramiko.RSAKey.from_private_key_file("." + ssh_private_key.url)
                        ssh.connect(str(server_ip), username=ssh_user, pkey = key, timeout=6000)
                    except Exception as e:
                        show_error(e)

                    for j in BackupInstance.objects.filter(backup__exact=i.name):
                        try:
                            (ssh_stdin, ssh_stdout, ssh_stderr) = ssh.exec_command("ls " + str(i.fs_storage) + " | grep -q ^" + j.file_name + "$")
                            exit_status = ssh_stdout.channel.recv_exit_status()
                            if exit_status == 1:
                                j.delete()
                                print("delete: " + str(i.fs_storage) + "/" + j.file_name)
                        except Exception as e:
                            show_error(e)
                        connection.close()

                    cmd = "ls " + str(i.fs_storage) + " | grep " + i.name
                    # Do command
                    (ssh_stdin, ssh_stdout, ssh_stderr) = ssh.exec_command(cmd)
                    # Get status code of command
                    # exit_status = ssh_stdout.channel.recv_exit_status()
                    # Print status code
                    # print("exit status: %s" % exit_status)
                    # Print content
                    for line in ssh_stdout.readlines():
                        try:
                            filename = line.rstrip()
                            # (ssh_stdin1, ssh_stdout1, ssh_stderr1) = ssh.exec_command("stat -c %Z " + str(i.fs_storage) + filename)
                            (ssh_stdin1, ssh_stdout1, ssh_stderr1) = ssh.exec_command('if [ "$(stat -c %F ' + str(i.fs_storage) + "/" + filename + ')" == "directory" ]; then find ' + str(i.fs_storage) + "/" + filename + ' -type f -daystart -print0 | xargs -0 stat -c %Y | sort -nr | head -1' + '; else stat -c %Y ' + str(i.fs_storage) + "/" + filename + '; fi')
                            try:
                                date_str = ssh_stdout1.readlines()[0].rstrip()
                            except:
                                continue
                            # (ssh_stdin2, ssh_stdout2, ssh_stderr2) = ssh.exec_command("stat -c %s " + str(i.fs_storage) + filename)
                            (ssh_stdin2, ssh_stdout2, ssh_stderr2) = ssh.exec_command("du --byte -s " + str(i.fs_storage) + "/" + filename + " | awk '{print $1}'")
                            size = ssh_stdout2.readlines()[0].rstrip()
                            date = datetime.datetime.fromtimestamp(int(date_str), pytz.timezone(env.TIME_ZONE))
                            connection.close()
                            BackupInstance.objects.update_or_create(backup=i, file_name=filename, defaults={'date': date, 'size': int(size)})
                            print("create or update: " + str(i.fs_storage) + "/" + filename)
                        except Exception as e:
                            show_error(e)
                        connection.close()

                    # Close ssh connect
                    ssh.close()

                else:
                    pass
            except Exception as e:
                show_error(e)
    except Exception as e:
        show_error(e)

    send_mail()


@kronos.register('0 0 * * *')
def delete_tmp_report():
    folder = 'reports'
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            show_error(e)