from django.db import models


class Continent(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Country(models.Model):
    name = models.CharField(max_length=50)
    continent = models.ForeignKey(Continent)
    is_cold = models.BooleanField(choices=[(True, 'Yes'), (False, 'No')])
    population = models.PositiveIntegerField(blank=True, null=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'

    def __str__(self):
        return self.name
