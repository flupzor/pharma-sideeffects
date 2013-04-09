from django.db import models

class SideEffect(models.Model):
    name = models.CharField(max_length=64, verbose_name='name', db_index=True)
    meddra_name = models.CharField(max_length=64, verbose_name='name')

class Drug(models.Model):
    name = models.CharField(max_length=64, verbose_name='name', db_index=True)

    flat_compound_id = models.CharField(max_length=64, verbose_name='name', db_index=True)
    stereo_compound_id = models.CharField(max_length=64, verbose_name='name', db_index=True)

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

    class Meta:
        unique_together = ('drug', 'side_effect',)

