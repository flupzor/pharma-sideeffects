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

import sys

from django.core.management import setup_environ
from django import db

from drugs.models import *
import settings

setup_environ(settings)

class ParseLine(object):
    def __init__(self):
        self.columns = {}

    def __getattr__(self, name):
        return self.columns[name]
        
    def parse(self, line):
        split_line = line.split("\t")

        for i in range(len(split_line)):
            self.columns[self.column_names[i]] = split_line[i] 

    def __str__(self):
        s = ''

        for name, value in self.columns.items():
            s += "%s: %s, " % (name, value)

        return s

class LabelMappingLine(ParseLine):
    column_names = [ 'generic_name', 'brand_name', 'marker', 'compound_id1',
        'compound_id2', 'url', 'label_identifier']

class MeddraFreqParsedLine(ParseLine):
    column_names = ['flat_compound_id', 'stereo_compound_id', 'source_label',
        'umls_concept_id', 'concept_name', 'placebo', 'frequency_description',
        'lower_bound_frequency', 'upper_bound_frequency',
        'MedDRA_concept_type', 'UMLS_concept_id_for_MedDRA_term',
        'MedDRA_side_effect_name']

class MeddraAdverseEffectLine(ParseLine):
    column_names = ['flat_compound_id', 'stereo_compound_id', 'umls_concept_id', \
        'drug_name', 'side_effect_name', 'MedDRA_concept_type', \
        'UMLS_concept_id_for_MedDRA_term', 'MedDRA_side_effect_name' ]

def for_every_line(filename, cb):

    sys.stdout.write("Opening file: %s\n" %(filename, ))

    f = open(filename, 'r')

    # Calculate the number of lines. Which will be used to show the progress.
    line_count = 0
    while True:
        line = f.readline()

        # End of file
        if line == "":
            break

        line_count += 1

    # Reset read pointer
    f.seek(0)

    line_number = 1
    while True:
        line = f.readline()

        # End of file
        if line == "":
            break

        # Skip empty lines
        if (line.isspace()):
            continue

        # Trim newlines and such
        line = line.rstrip();

        sys.stdout.write("Processing line: %d of %d %f%%\r" % (line_number, line_count,
            float(line_number) / float(line_count) * 100.0))
        sys.stdout.flush()

        cb(line)

        line_number += 1

        # Clear the list of SQL queries Django keeps.
        db.reset_queries()

def adverse_effect_line(line):
    effect_line = MeddraAdverseEffectLine()
    effect_line.parse(line)

    try:
        side_effect = SideEffect.objects.get(name = effect_line.side_effect_name)
    except SideEffect.DoesNotExist:
        side_effect = SideEffect()

    side_effect.name = effect_line.side_effect_name
    side_effect.meddra_name = effect_line.MedDRA_side_effect_name 

    side_effect.save()

    try:
        drug = Drug.objects.get(name = effect_line.drug_name)
    except Drug.DoesNotExist:
        drug = Drug()

    drug.name = effect_line.drug_name
    drug.flat_compound_id = effect_line.flat_compound_id
    drug.stereo_compound_id = effect_line.stereo_compound_id

    drug.save()

    try:
        side_effect_freq = SideEffectFrequency.objects.get(side_effect = side_effect, drug = drug)
    except SideEffectFrequency.DoesNotExist:
        side_effect_freq = SideEffectFrequency(side_effect = side_effect, drug = drug)

    side_effect_freq.save()

def meddra_freq_parsed_line(line):
    freq_line = MeddraFreqParsedLine()
    freq_line.parse(line)

    try:
        side_effect = SideEffect.objects.get(name = freq_line.concept_name)
    except SideEffect.DoesNotExist:
        side_effect = SideEffect()

    side_effect.save()

    try:
        drug = Drug.objects.get(stereo_compound_id = freq_line.stereo_compound_id)
    except Drug.DoesNotExist:
        drug = Drug()

    drug.save()

    try:
        side_effect_freq = SideEffectFrequency.objects.get(side_effect = side_effect, drug = drug)
    except SideEffectFrequency.DoesNotExist:
        side_effect_freq = SideEffectFrequency(side_effect = side_effect, drug = drug)

    side_effect_freq.frequency_description = freq_line.frequency_description
    side_effect_freq.frequency_lower = freq_line.lower_bound_frequency
    side_effect_freq.frequency_upper = freq_line.upper_bound_frequency

    side_effect_freq.save()

def label_mapping_line(line):
        label_line = LabelMappingLine()
        label_line.parse(line)

        drug = Drug()

        drug.generic_name = label_line.generic_name
        drug.brand_name = label_line.brand_name

        drug.save()

if __name__ == '__main__':

# XXX: For now, we aren't using the label mappings
#    for_every_line('sideeffects_files/label_mapping.tsv', label_mapping_line) 
    for_every_line('sideeffects_files/meddra_adverse_effects.tsv', adverse_effect_line) 
    for_every_line('sideeffects_files/meddra_freq_parsed.tsv', meddra_freq_parsed_line) 
