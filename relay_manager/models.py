from django.db import models

# Create your models here.


class RelayNodes(models.Model):
    ip = models.GenericIPAddressField()
    port = models.IntegerField()
    owner = models.CharField(default='NA', max_length=100)
    email = models.EmailField()
    type = models.CharField(default='Ark', max_length=100)

    def __str__(self):
        return self.ip
