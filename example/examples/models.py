from __future__ import unicode_literals

from django.db import models

# Create your models here.

class User(models.Model):

  name = models.CharField(max_length=20)
  session = models.CharField(max_length=20)
  # isOnline = models.BooleanField(default=false)

  class Meta:
    ordering = ('name',)

  def __unicode__(self):
    return self.name
