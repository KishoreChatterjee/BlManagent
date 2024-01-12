from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class Author(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(default="")

class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author,on_delete=models.CASCADE)


class User(AbstractUser):
    email = models.EmailField(unique=True)
    canCreateAuthor = models.BooleanField(default=False)

    def __str__(self):
        return self.username    