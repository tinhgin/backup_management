import kronos
from .models import Backup, BackupInstance, FSPath, FSStorage, S3Storage
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
import boto3
from operator import itemgetter

logger = logging.getLogger('BACKUP-MANAGEMENT')
logging.basicConfig(stream=sys.stdout, level=logging.ERROR)


@kronos.register(env.CRONJOB)
def update_backup_instances_job():
    try:
        backups = Backup.objects.all()
        for i in backups:
            if i.keep == None:
                keep = 35
            else:
                keep = i.keep
            # if i.storage_type == "fs":
            #     continue
            try:
                if i.storage_type == "fs" and i.fs_storage != None:
                    try:
                        fs_path = (str(i.fs_storage)).split(":")[1]
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
                        ssh.connect(str(server_ip), username=ssh_user, pkey=key, timeout=6000)
                    except Exception as e:
                        show_error(e)

                    try:
                        (ssh_stdin, ssh_stdout, ssh_stderr) = ssh.exec_command(
                            "ls " + fs_path + " | grep " + i.name)
                        fs_files = ssh_stdout.readlines()
                        fs_file_count = len(fs_files)
                        if fs_file_count > keep:
                            num_to_del = fs_file_count - keep
                            d_list = []
                            for k in fs_files:
                                k = k.rstrip()
                                d_dict = {}
                                d_dict['file'] = k

                                (ssh_stdin1, ssh_stdout1, ssh_stderr1) = ssh.exec_command(
                                    'if [ "$(stat -c %F ' + fs_path + "/" + k + ')" == "directory" ]; then find ' + fs_path + "/" + k + ' -type f -daystart -print0 | xargs -0 stat -c %Y | sort -nr | head -1' + '; else stat -c %Y ' + fs_path + "/" + k + '; fi')
                                try:
                                    date_str = ssh_stdout1.readlines()[0].rstrip()
                                except:
                                    continue
                                d_dict['date'] = datetime.datetime.fromtimestamp(int(date_str),
                                                                                 pytz.timezone(env.TIME_ZONE))
                                d_list.append(d_dict)

                            sorted_d_list = sorted(d_list, key=itemgetter('date'))
                            list_to_del = sorted_d_list[0:num_to_del]
                            for j in list_to_del:
                                try:
                                    ssh.exec_command("rm -rf " + fs_path + "/" + j['file'])
                                    print("delete on server: " + fs_path + "/" + j['file'])
                                except Exception as e:
                                    show_error(e)
                    except Exception as e:
                        show_error(e)

                    for j in BackupInstance.objects.filter(backup__exact=i.name):
                        try:
                            (ssh_stdin, ssh_stdout, ssh_stderr) = ssh.exec_command(
                                "ls " + fs_path + " | grep -q ^" + j.file_name + "$")
                            exit_status = ssh_stdout.channel.recv_exit_status()
                            if exit_status == 1:
                                j.delete()
                                print("delete: " + fs_path + "/" + j.file_name)
                        except Exception as e:
                            show_error(e)
                        connection.close()

                    cmd = "ls " + fs_path + " | grep " + i.name
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
                            (ssh_stdin1, ssh_stdout1, ssh_stderr1) = ssh.exec_command(
                                'if [ "$(stat -c %F ' + fs_path + "/" + filename + ')" == "directory" ]; then find ' + fs_path + "/" + filename + ' -type f -daystart -print0 | xargs -0 stat -c %Y | sort -nr | head -1' + '; else stat -c %Y ' + fs_path + "/" + filename + '; fi')
                            try:
                                date_str = ssh_stdout1.readlines()[0].rstrip()
                            except:
                                continue
                            (ssh_stdin2, ssh_stdout2, ssh_stderr2) = ssh.exec_command(
                                "du --byte -s " + fs_path + "/" + filename + " | awk '{print $1}'")
                            size = ssh_stdout2.readlines()[0].rstrip()
                            date = datetime.datetime.fromtimestamp(int(date_str), pytz.timezone(env.TIME_ZONE))
                            connection.close()
                            BackupInstance.objects.update_or_create(backup=i, file_name=filename,
                                                                    defaults={'date': date, 'size': int(size)})
                            print("create or update: " + fs_path + "/" + filename)
                        except Exception as e:
                            show_error(e)
                        connection.close()

                    # Close ssh connect
                    ssh.close()

                elif i.storage_type == "s3" and i.s3_storage != None:
                    try:
                        for k in S3Storage.objects.all():
                            if str(k.endpoint) in str(i.s3_storage) and str(k.bucket) in str(i.s3_storage):
                                aws_access_key_id = k.access_key_id
                                aws_secret_access_key = k.secret_access_key
                                endpoint_url = str(k.endpoint)
                                bucket = str(k.bucket)
                    except Exception as e:
                        show_error(e)
                    s3_resource = boto3.resource(
                        service_name='s3',
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key,
                        endpoint_url=endpoint_url,
                    )
                    s3_client = boto3.client(
                        service_name='s3',
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key,
                        endpoint_url=endpoint_url,
                    )
                    s3_path = (str(i.s3_storage)).split(bucket)[1]
                    if s3_path[0] == "/":
                        s3_path = s3_path[1:len(s3_path)]

                    try:
                        s3_list = []
                        for n in s3_client.list_objects(Bucket=bucket)['Contents']:
                            s3_dict = {}
                            if s3_path + "/" + i.name in n['Key']:
                                s3_dict['name'] = n['Key']
                                s3_dict['date'] = n['LastModified']
                                s3_list.append(s3_dict)


                        if len(s3_list) > keep:
                            s3num_to_del = len(s3_list) - keep
                            sorted_s3_list = sorted(s3_list, key=itemgetter('date'))
                            s3list_to_del = sorted_s3_list[0:s3num_to_del]
                            for s3_key_to_del in s3list_to_del:
                                try:
                                    s3_resource.Object(bucket, s3_key_to_del['name']).delete()
                                    print("delete on S3: " + endpoint_url + "/" + bucket + "/" + s3_path + '/' + j.file_name)
                                except Exception as e:
                                    show_error(e)
                    except Exception as e:
                        show_error(e)

                    for j in BackupInstance.objects.filter(backup__exact=i.name):
                        try:
                            try:
                                s3_resource.Object(bucket, s3_path + '/' + j.file_name).load()
                            except:
                                j.delete()
                                connection.close()
                                print("delete: " + endpoint_url + "/" + bucket + "/" + s3_path + '/' + j.file_name)
                        except Exception as e:
                            show_error(e)

                    for m in s3_client.list_objects(Bucket=bucket)['Contents']:
                        try:
                            if s3_path + "/" + i.name in m['Key']:
                                s3filename = m['Key'].split("/")[-1]
                                s3date = m['LastModified']
                                s3size = m['Size']
                                BackupInstance.objects.update_or_create(backup=i, file_name=s3filename,
                                                                        defaults={'date': s3date, 'size': int(s3size)})
                                connection.close()
                                print(
                                    "create or update: " + endpoint_url + "/" + bucket + "/" + s3_path + '/' + s3filename)
                        except Exception as e:
                            show_error(e)

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
