from django.db import models
import os
import shutil

def upload_to(instance, filename):
    if not os.path.exists('uploads/'):
        os.makedirs('uploads/')
    else:
        shutil.rmtree('uploads/')
        os.makedirs('uploads/')
    return os.path.join('uploads/', filename)


class File(models.Model):
    file = models.FileField(upload_to=upload_to)

