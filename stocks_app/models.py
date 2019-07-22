from django.db import models

# Create your models here.


class Stock(models.Model):

    id = models.AutoField(primary_key=True)
    title = models.TextField()
    stock_count = models.IntegerField()

    class Meta:
        db_table = "stock"
