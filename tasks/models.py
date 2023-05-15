from django.db import models
import os
from django.core.files.storage import FileSystemStorage

"""
def upload_to(instance, filename):
    base_path = 'media/uploads'

    if not os.path.exists(base_path):
        os.makedirs(base_path)
    else:
        shutil.rmtree(base_path)
        os.makedirs(base_path)
    return os.path.join(base_path, filename)

"""


def overwrite_upload_to(instance, filename):
    fs = FileSystemStorage()
    if fs.exists(filename):
        fs.delete(filename)
    return filename


class File(models.Model):
    Statement = models.FileField(upload_to=overwrite_upload_to)
    Cheques = models.FileField(upload_to=overwrite_upload_to)
    Direct_Debit = models.FileField(upload_to=overwrite_upload_to)
    EFTs = models.FileField(upload_to=overwrite_upload_to)


class Donor(models.Model):
    name = models.CharField(max_length=100)
    donation = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class StatFile(models.Model):
    Statement = models.FileField(upload_to=overwrite_upload_to)
