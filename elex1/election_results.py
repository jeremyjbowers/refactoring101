#!/usr/bin/env python
"""
A monstrosity of an election results script. Generates statewide results for races, 
based on county results.

This module bundles together way too much functionality and is near impossible to test,
beyond eye-balling results.

USAGE:

    python election_results.py


OUTPUT:

    Generates summary_results.csv


"""
import csv
import datetime
import urllib
from decimal import Decimal, getcontext
from operator import itemgetter
from collections import defaultdict
from os.path import abspath, dirname, join
from urllib import urlretrieve

# Set precision for all Decimals
getcontext().prec = 2

# Download CSV of fake Virginia election results from GDocs
url = "https://docs.google.com/spreadsheet/pub?key=0AhhC0IWaObRqdGFkUW1kUmp2ZlZjUjdTYV9lNFJ5RHc&output=csv"

# Download the file to the root project directory /path/to/refactorin101/
# NOTE: This will only download the file if it doesn't already exist
# This approach is simplified for demo purposes. In a real-life application,
# you'd likely have a considerable amount of additional code
# to appropriately handle HTTP timeouts, 404s, and other real-world scenarios.
# For example, you might retry a request several times after a timeout, and then
# send an email alert that the site is non-responsive.
filename = join(dirname(dirname(abspath(__file__))), 'fake_va_elec_results.csv')
urllib.urlretrieve(url, filename)

# Create reader for ingesting CSV as array of dicts
reader = csv.DictReader(open(filename, 'rb'))

# Normally, accessing a non-existent dictionary key would raise a KeyError.
# Use defaultdict to automatically create non-existent keys with an empty dictionary as the default value.
# See https://pydocs2cn.readthedocs.org/en/latest/library/collections.html#defaultdict-objects
results = defaultdict(dict)

# Initial data clean-up
for row in reader:
    # Parse name into first and last
    row['last_name'], row['first_name'] = [name.strip() for name in row['candidate'].split(',')]

    # Standardize party abbreviations
    party = row['party'].strip().upper()
    if party.startswith('GOP'):
        party_clean = 'REP'
    elif party.startswith('DEM'):
        party_clean = 'DEM'
    else:
        party_clean = party
    row['party_clean'] = party_clean

    # Standardize Office and district
    office = row['office']
    if 'Rep' in office:
        row['office_clean'] = 'U.S. House of Representatives'
        row['district'] = int(office.split('-')[-1])
    else:
        row['office_clean'] = office.strip()
        row['district'] = ''

    # Convert total votes to an integer
    row['votes'] = int(row['votes'])

    # Store county-level results by office/district pair, then by candidate key
    # Create unique candidate key from party and name, in case multiple candidates have same
    race_key = (row['office'], row['district'])
    cand_key = (row['party'], row['candidate'])
    # Below, setdefault initializes empty dict and list for the respective keys if they don't already exist.
    race = results[race_key]
    race.setdefault(cand_key, []).append(row)


# Create a new set of summary results that includes each candidate's
# statewide total votes, % of vote, winner flag, margin of victory, tie_race flag
summary = defaultdict(dict)

for race_key, cand_results in results.items():
    all_votes = 0
    tie_race = ''
    cand_totals = []
    for cand_key, results in cand_results.items():
        # Populate a new candidate dict using one set of county results
        cand = {
            'candidate': results[0]['candidate'],
            'first_name': results[0]['first_name'],
            'last_name': results[0]['last_name'],
            'party': results[0]['party'],
            'party_clean': results[0]['party_clean'],
            'winner': '',
            'margin_of_vic': '',
        }
        # Calculate candidate total votes
        cand_statewide_total= sum([result['votes'] for result in results])
        cand['votes'] = cand_statewide_total
        cand_totals.append(cand)
        # Add cand totals to racewide vote count
        all_votes += cand_statewide_total

    # sort cands from highest to lowest vote count
    sorted_cands = sorted(cand_totals, key=itemgetter('votes'), reverse=True)

    # Determine vote pct for each candiate
    for cand in sorted_cands:
        vote_pct = (Decimal(cand['votes']) / Decimal(all_votes)) * 100
        cand['vote_pct'] = "%s" %  vote_pct.to_eng_string()

    # Determine winner, if any, and assign margin of victory
    first = sorted_cands[0]
    second = sorted_cands[1]

    if first['votes'] == second['votes']:
        tie_race = 'X'
    else:
        first['winner'] = 'X'
        mov = (Decimal(first['votes'] - second['votes']) / all_votes) * 100
        first['margin_of_vic'] = "%s" % mov.to_eng_string()

    # Get race metadata from one set of results
    result = cand_results.values()[0][0]
    summary[race_key] = {
        'all_votes': all_votes,
        'tie_race': tie_race,
        'date': result['date'],
        'office': result['office_clean'],
        'district': result['district'],
        'candidates': sorted_cands,
    }


# Output CSV of summary results
outfile = join(dirname(abspath(__file__)), 'summary_results.csv')
with open(outfile, 'wb') as fh:
    # We'll limit the output to cleanly parsed, standardized values
    fieldnames = [
        'date',
        'office',
        'district',
        'last_name',
        'first_name',
        'party_clean',
        'all_votes',
        'votes',
        'vote_pct',
        'winner',
        'margin_of_vic',
        'tie_race',
    ]
    writer = csv.DictWriter(fh, fieldnames, extrasaction='ignore', quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
    for race, results in summary.items():
        cands = results.pop('candidates')
        for cand in cands:
            results.update(cand)
            writer.writerow(results)
