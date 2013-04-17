# Copyright (c) 2013 Alexander Schrijver <alex@flupzor.nl>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

from django.db import models

from django.db.models.signals import post_save

# Copied from: https://github.com/smn/django-dirtyfields/blob/master/src/dirtyfields/dirtyfields.py
# Adapted from http://stackoverflow.com/questions/110803/dirty-fields-in-django

class DirtyFieldsMixin(object):
    def __init__(self, *args, **kwargs):
        super(DirtyFieldsMixin, self).__init__(*args, **kwargs)
        post_save.connect(reset_state, sender=self.__class__, 
                            dispatch_uid='%s-DirtyFieldsMixin-sweeper' % self.__class__.__name__)
        reset_state(sender=self.__class__, instance=self)

    def _as_dict(self):
        return dict([(f.name, getattr(self, f.name)) for f in self._meta.local_fields if not f.rel])
    
    def get_dirty_fields(self):
        new_state = self._as_dict()
        return dict([(key, value) for key, value in self._original_state.iteritems() if value != new_state[key]])
    
    def is_dirty(self):
        # in order to be dirty we need to have been saved at least once, so we
        # check for a primary key and we need our dirty fields to not be empty
        if not self.pk: 
            return True
        return {} != self.get_dirty_fields()

def reset_state(sender, instance, **kwargs):
    instance._original_state = instance._as_dict()

class SideEffect(DirtyFieldsMixin, models.Model):
    name = models.CharField(max_length=64, verbose_name='name', db_index=True)
    meddra_name = models.CharField(max_length=64, verbose_name='name')
    umls_concept_id = models.CharField(max_length=64, verbose_name='name', db_index=True, unique=True)

class Drug(DirtyFieldsMixin, models.Model):
    name = models.CharField(max_length=64, verbose_name='name', db_index=True)

    atc_code = models.CharField(max_length=64, verbose_name='ATC code')

    flat_compound_id = models.CharField(max_length=64, verbose_name='name', db_index=True)
    stereo_compound_id = models.CharField(max_length=64, verbose_name='name', db_index=True)

    side_effects = models.ManyToManyField(SideEffect, through =
        'SideEffectFrequency', blank=True, null=True,
        verbose_name='side effects')

    missing_info = models.BooleanField(default=False)

    class Meta:
        unique_together = ('flat_compound_id', 'stereo_compound_id')

class SideEffectFrequency(DirtyFieldsMixin, models.Model):
    drug = models.ForeignKey(Drug, blank=True, null=True)
    side_effect = models.ForeignKey(SideEffect, blank=True, null=True)
    frequency_description = models.CharField(max_length=64, verbose_name='Frequency description')
    frequency_lower = models.FloatField(blank=True,null=True)
    frequency_upper = models.FloatField(blank=True,null=True)

    class Meta:
        unique_together = ('drug', 'side_effect',)

