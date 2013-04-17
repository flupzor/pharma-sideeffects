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
from django.db import connection

from drugs.models import *
import settings

import time

setup_environ(settings)

class ParseLine(object):
    def __init__(self):
        self.columns = {}

    def __getattr__(self, name):
        return self.columns[name]
        
    def parse(self, line):
        # XXX: Ignore commented lines.
        split_line = line.split("\t")

        if len(split_line) != len(self.column_names):
            raise SyntaxError("Too little or too many columns found.");

        for i in range(len(split_line)):
            self.columns[self.column_names[i]] = split_line[i] 

    def __str__(self):
        s = ''

        for name, value in self.columns.items():
            s += "%s: %s, " % (name, value)

        return s

class ChemicalSources(ParseLine):
    column_names = ['flat_compound_id', 'stereo_compound_id', 'source', 'id']

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
    per_cent = 0
    time_started = time.time()
    lines_per_sec = 0
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

        # Print a progress line every second
        if time.time() - time_started >= 1:
            per_cent = round(float(line_number) / float(line_count) * 100.0, 2)

            sys.stdout.write("Processing line: %d of %d %f%% (%d lps)\r" % (line_number, \
                line_count, per_cent, lines_per_sec))
            sys.stdout.flush()

            time_started = time.time()
            lines_per_sec = 0

        cb(line)

        line_number += 1
        lines_per_sec += 1

        # Clear the list of SQL queries Django keeps.
        db.reset_queries()

global_cache = { 'SideEffect': {}, 'Drug': {}, 'SideEffectFrequency': {}}

if 0:
    def cache_or_create(klass, **kwargs):
        return klass.objects.get_or_create(**kwargs)
else:
    def cache_or_create(klass, **kwargs):
        class_name = klass.__name__
        cache = global_cache[class_name]
        created = False

        # Python can't hash a dictionary, instead use an ordered tuple of
        # tuples, which can be hashed. The .items method gives an ordered list
        # back, so we should be fine.
        cache_key = tuple(kwargs.items())

        if cache_key in cache:
            cached_item = cache[cache_key]
        else:
            created = True
            cached_item = klass(**kwargs)
            cached_item.save()

            cache[cache_key] = cached_item

        return cached_item, created

def adverse_effect_line(line):
    effect_line = MeddraAdverseEffectLine()
    effect_line.parse(line)

    side_effect, created = cache_or_create(SideEffect, umls_concept_id = effect_line.umls_concept_id)

    side_effect.name = effect_line.side_effect_name
    side_effect.meddra_name = effect_line.MedDRA_side_effect_name 

    if side_effect.is_dirty():
        side_effect.save()

    drug, created = cache_or_create(Drug, stereo_compound_id =
        effect_line.stereo_compound_id, flat_compound_id =
        effect_line.flat_compound_id)

    drug.name = effect_line.drug_name
    drug.flat_compound_id = effect_line.flat_compound_id
    drug.stereo_compound_id = effect_line.stereo_compound_id

    if drug.is_dirty():
        drug.save()

    side_effect_freq, created = cache_or_create(SideEffectFrequency, side_effect =
        side_effect, drug = drug)

def meddra_freq_parsed_line(line):
    freq_line = MeddraFreqParsedLine()
    freq_line.parse(line)

    side_effect, created = cache_or_create(SideEffect, umls_concept_id =
        freq_line.umls_concept_id)

    drug, created = cache_or_create(Drug, stereo_compound_id =
        freq_line.stereo_compound_id, flat_compound_id =
        freq_line.flat_compound_id)

    side_effect_freq, created = cache_or_create(SideEffectFrequency, side_effect =
        side_effect, drug = drug)

    side_effect_freq.frequency_description = freq_line.frequency_description
    side_effect_freq.frequency_lower = freq_line.lower_bound_frequency
    side_effect_freq.frequency_upper = freq_line.upper_bound_frequency

    if side_effect_freq.is_dirty():
        side_effect_freq.save()

def label_mapping_line(line):
    label_line = LabelMappingLine()
    label_line.parse(line)

    drug = Drug()

    drug.generic_name = label_line.generic_name
    drug.brand_name = label_line.brand_name

    drug.save()

def atc_line(line):
    try:
        sources = ChemicalSources()
        sources.parse(line)
    except SyntaxError as e:
        # The beginning of this file is 
        return;

    # We only care about ATC codes for now
    if sources.source != 'ATC':
        return;

    drug, created = cache_or_create(Drug, stereo_compound_id =
        sources.stereo_compound_id, flat_compound_id =
        sources.flat_compound_id)

    drug.atc_code = sources.id;

    if drug.is_dirty():
        drug.save()

if __name__ == '__main__':

    # XXX: Is there always one connecetion? And does it get closed?
    cursor = connection.cursor()

    cursor.execute("PRAGMA cache_size = 900000;");
    cursor.execute("PRAGMA journal_mode = MEMORY;");

# XXX: For now, we aren't using the label mappings
#    for_every_line('sideeffects_files/label_mapping.tsv', label_mapping_line, {}) 

    for_every_line('sideeffects_files/meddra_adverse_effects.tsv',
        adverse_effect_line) 
    for_every_line('sideeffects_files/meddra_freq_parsed.tsv',
        meddra_freq_parsed_line) 
    for_every_line('sideeffects_files/chemical.sources.v3.1.tsv', atc_line)
