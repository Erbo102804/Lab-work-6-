from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse


class Product(models.Model):
    name = models.CharField('Название', max_length=100)
    description = models.TextField('Описание', blank=True)
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2,
                                validators=[MinValueValidator(0)])
    quantity = models.PositiveIntegerField('Количество', default=0)
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('crud:detail', args=[self.pk])
