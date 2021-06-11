from django.contrib import admin
from .models import BackupInstance, Project, S3Storage, FSStorage, S3Path, FSPath, Backup, TotalBackup

@admin.register(BackupInstance)
class BackupInstanceAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'backup', 'date', 'size')
    list_filter = ('backup', 'date')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    list_filter = ('name',)


@admin.register(S3Storage)
class S3StorageAdmin(admin.ModelAdmin):
    list_display = ('bucket', 'endpoint', 'region')
    list_filter = ('bucket', 'endpoint', 'region')


@admin.register(FSStorage)
class FSStorageAdmin(admin.ModelAdmin):
    list_display = ('server_ip', 'ssh_user')
    list_filter = ('server_ip', 'ssh_user')


@admin.register(S3Path)
class S3PathAdmin(admin.ModelAdmin):
    list_display = ('s3_path', 's3_bucket')
    list_filter = ('s3_path', 's3_bucket')


@admin.register(FSPath)
class FSPathAdmin(admin.ModelAdmin):
    list_display = ('fs_path', 'server_ip')
    list_filter = ('server_ip', 'fs_path')


@admin.register(Backup)
class BackupAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'storage_type', 'fs_storage', 's3_storage')
    list_filter = ('project', 'name', 'project', 'storage_type','fs_storage', 's3_storage')


@admin.register(TotalBackup)
class TotalBackupAdmin(admin.ModelAdmin):
    list_display = ('date', 'total')