#!/usr/bin/env python

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

from django.core.management import setup_environ
import settings
from drugs.models import *

setup_environ(settings)

import sys

if __name__ == '__main__':
    label_mapping = open('sideeffects_files/label_mapping.tsv', 'r')

# XXX: For now, we aren't using the label mappings

#    for line in label_mapping.readlines():
#
#        # Skip empty lines
#        if (len(line) == 0 or line.isspace()):
#            continue
#
#        generic_name, brand_name, marker, compound_id1, compound_id2, url, \
#            label_identifier = line.split('\t')
#
#        drug = Drug()
#
#        drug.generic_name = generic_name
#        drug.brand_name = brand_name
#
#        drug.save()
#

    meddra_adverse_effects = open('sideeffects_files/meddra_adverse_effects.tsv', 'r')

    for line in meddra_adverse_effects.readlines():

        # Skip empty lines
        if (len(line) == 0 or line.isspace()):
            continue

        flat_compound_id, stereo_compound_id, umls_concept_id, drug_name, \
            side_effect_name, MedDRA_concept_type, \
            UMLS_concept_id_for_MedDRA_term, \
            MedDRA_side_effect_name = line.split('\t')

        try:
            side_effect = SideEffect.objects.get(name = side_effect_name)
        except SideEffect.DoesNotExist:
            side_effect = SideEffect()

        side_effect.name = side_effect_name
        side_effect.meddra_name = MedDRA_side_effect_name 

        side_effect.save()

        try:
            drug = Drug.objects.get(name = drug_name)
        except Drug.DoesNotExist:
            drug = Drug()

        drug.name = drug_name
        drug.flat_compound_id = flat_compound_id
        drug.stereo_compound_id = stereo_compound_id

        drug.save()

        try:
            side_effect_freq = SideEffectFrequency.objects.get(side_effect = side_effect, drug = drug)
        except SideEffectFrequency.DoesNotExist:
            side_effect_freq = SideEffectFrequency(side_effect = side_effect, drug = drug)

        side_effect_freq.save()

    meddra_freq_parsed  = open('sideeffects_files/meddra_freq_parsed.tsv', 'r')

    for line in meddra_freq_parsed.readlines():

        # Skip empty lines
        if (len(line) == 0 or line.isspace()):
            continue

        flat_compound_id, stereo_compound_id, source_label, umls_concept_id, concept_name, placebo, \
            frequency_description, lower_bound_frequency, \
            upper_bound_frequency, MedDRA_concept_type, \
            UMLS_concept_id_for_MedDRA_term, \
            MedDRA_side_effect_name = line.split('\t')

        try:
            side_effect = SideEffect.objects.get(meddra_name = MedDRA_side_effect_name)
        except SideEffect.DoesNotExist:
            side_effect = SideEffect()

        side_effect.save()

        try:
            drug = Drug.objects.get(stereo_compound_id = stereo_compound_id)
        except Drug.DoesNotExist:
            drug = Drug()

        drug.save()

        try:
            side_effect_freq = SideEffectFrequency.objects.get(side_effect = side_effect, drug = drug)
        except SideEffectFrequency.DoesNotExist:
            side_effect_freq = SideEffectFrequency(side_effect = side_effect, drug = drug)

        side_effect_freq.frequency_description = frequency_description
        side_effect_freq.frequency_lower = lower_bound_frequency
        side_effect_freq.frequency_upper = upper_bound_frequency

        side_effect_freq.save()

