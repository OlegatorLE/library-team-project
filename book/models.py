from django.db import models


class Book(models.Model):
    """Model representing a book in the library."""
    class CoverChoices(models.TextChoices):
        HARD = "hard"
        SOFT = "soft"

    title = models.CharField(max_length=64)
    author = models.CharField(max_length=64)
    cover = models.CharField(max_length=4, choices=CoverChoices.choices)
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(decimal_places=2, max_digits=10)

    class Meta:
        ordering = ["title"]
        unique_together = ("title", "author")

    def __str__(self):
        return self.title
