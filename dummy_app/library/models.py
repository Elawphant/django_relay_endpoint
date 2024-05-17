from django.db import models

# Create your models here.


class Author(models.Model):
    name = models.CharField(max_length=20)
    books = models.ManyToManyField(to="library.Book", related_name='authors', blank=True)

class Shelf(models.Model):
    number = models.PositiveIntegerField()

class Book(models.Model):
    shelf = models.ForeignKey(to='library.Shelf', related_name="books", on_delete=models.CASCADE)

class BookInfo(models.Model):
    book = models.OneToOneField(to='library.Book', on_delete=models.CASCADE)
    title = models.CharField(max_length=20)
    subtitle = models.CharField(max_length=20, blank=True)
    pages = models.PositiveIntegerField()
    is_novel = models.BooleanField()
    publication_date = models.DateField()



