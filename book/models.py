from random import choices

from django.db import models
from django.conf import settings

# Create your models here.


class Book(models.Model):
    class CoverChoice(models.TextChoices):
        HARD = "Hard"
        SOFT = "Soft"

    title = models.CharField(max_length=155)
    author = models.CharField(max_length=255)
    cover = models.CharField(choices=CoverChoice.choices)
    inventory = models.IntegerField()
    daily_fee = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.title} by {self.author}"

    class Meta:
        ordering = ["title"]
