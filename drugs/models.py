from django.db import models

class SideEffect(models.Model):
    name = models.CharField(max_length=64, verbose_name='name')
    meddra_name = models.CharField(max_length=64, verbose_name='name')

class Drug(models.Model):
    name = models.CharField(max_length=64, verbose_name='name')

    flat_compound_id = models.CharField(max_length=64, verbose_name='name')
    stereo_compound_id = models.CharField(max_length=64, verbose_name='name')

    side_effects = models.ManyToManyField(SideEffect, through =
        'SideEffectFrequency', blank=True, null=True,
        verbose_name='side effects')

#    generic_name = models.CharField(max_length=64, verbose_name='name')
#    brand_name = models.CharField(max_length=64, verbose_name='name')

class SideEffectFrequency(models.Model):
    drug = models.ForeignKey(Drug, blank=True, null=True)
    side_effect = models.ForeignKey(SideEffect, blank=True, null=True)
    frequency_description = models.CharField(max_length=64, verbose_name='Frequency description')
    frequency_lower = models.FloatField(blank=True,null=True)
    frequency_upper = models.FloatField(blank=True,null=True)
