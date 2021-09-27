from django.db import models
from django.urls import reverse
import uuid


class Project(models.Model):
    name = models.CharField(max_length=100, primary_key=True)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        """Returns the url to access a particular project instance."""
        return reverse('project-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return '{0}'.format(self.name)


class S3Storage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    bucket = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    endpoint = models.CharField(max_length=100, null=True, blank=True)
    access_key_id = models.CharField(max_length=100)
    secret_access_key = models.CharField(max_length=100)

    class Meta:
        ordering = ['bucket']

    def get_absolute_url(self):
        """Returns the url to access a particular project instance."""
        return reverse('s3storage-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return '{0}/{1}'.format(self.endpoint, self.bucket)


class FSStorage(models.Model):
    server_ip = models.GenericIPAddressField(primary_key=True)
    ssh_user = models.CharField(max_length=50, default='backup')
    ssh_private_key = models.FileField(upload_to='uploads/')

    class Meta:
        ordering = ['server_ip']

    def get_absolute_url(self):
        """Returns the url to access a particular project instance."""
        return reverse('fsstorage-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return '{0}'.format(self.server_ip)


class S3Path(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    s3_path = models.CharField(max_length=100)
    s3_bucket = models.ForeignKey('S3Storage', on_delete=models.RESTRICT, null=True)

    class Meta:
        ordering = ['s3_path']

    def get_absolute_url(self):
        """Returns the url to access a particular project instance."""
        return reverse('s3path-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return '{0}{1}'.format(self.s3_bucket, self.s3_path)


class FSPath(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    fs_path = models.CharField(max_length=100)
    server_ip = models.ForeignKey('FSStorage', on_delete=models.RESTRICT, null=True)

    class Meta:
        ordering = ['fs_path']

    def get_absolute_url(self):
        """Returns the url to access a particular project instance."""
        return reverse('fspath-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return '{0}:{1}'.format(self.server_ip, self.fs_path)


class Backup(models.Model):
    name = models.CharField(max_length=200, primary_key=True)
    project = models.ForeignKey('Project', on_delete=models.RESTRICT, null=True)

    STORAGE_TYPE = (
        ('s3', 'S3'),
        ('fs', 'Filesystem'),
    )

    storage_type = models.CharField(
        max_length=2,
        choices=STORAGE_TYPE,
        blank=False,
        default='fs',
        help_text='Storage type: S3 or Filesystem')

    s3_storage = models.ForeignKey('S3Path', on_delete=models.RESTRICT, null=True, blank=True)
    fs_storage = models.ForeignKey('FSPath', on_delete=models.RESTRICT, null=True, blank=True)
    keep = models.PositiveIntegerField(default=35)


    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        """Returns the url to access a particular book instance."""
        return reverse('backup-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return self.name


class BackupInstance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                          help_text="Unique ID for this particular backup")
    backup = models.ForeignKey('Backup', on_delete=models.CASCADE, null=True)
    file_name = models.CharField(max_length=100, unique=True)
    date = models.DateTimeField(null=True, blank=True)
    size = models.PositiveBigIntegerField(null=True, blank=True)


    class Meta:
        ordering = ['date']

    def get_absolute_url(self):
        """Returns the url to access a particular project instance."""
        return reverse('backupinstance-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return '{0} ({1})'.format(self.id, self.backup.name)

class TotalBackup(models.Model):
    date = models.DateField(unique=True)
    total = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return str(self.date)
