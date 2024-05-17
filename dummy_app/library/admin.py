from django.contrib import admin
from library.models import Author, Book, BookInfo, Shelf

# Register your models here.
admin.site.register([Author, Book, BookInfo, Shelf])