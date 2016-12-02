#!/usr/bin/env python2

from __future__ import print_function, division, absolute_import

# Load config, utils, venv
import os.path
import imp
my_dir = os.path.dirname(os.path.abspath(__file__))
utils = imp.load_source('utils', os.path.join(my_dir, '../utils.py'))
conf = utils.conf
utils.activate_virtualenv()

import os
import multiprocessing

echo = utils.get_path('echo')
tabix = utils.get_path('tabix')
bgzip = utils.get_path('bgzip')

tmp_dir = os.path.join(conf.data_dir, 'tmp')
augmented_pheno_dir = os.path.join(conf.data_dir, 'augmented_pheno')
augmented_pheno_gz_dir = os.path.join(conf.data_dir, 'augmented_pheno_gz')

def convert(infile):
    fname = os.path.basename(infile) + '.gz'
    tmpfile = os.path.join(tmp_dir, 'augmented_pheno_gz' + fname)
    outfile = os.path.join(augmented_pheno_gz_dir, fname)
    tbifile = os.path.join(augmented_pheno_gz_dir, fname + '.tbi')
    print("{} -> {}".format(infile, outfile))
    if not os.path.exists(outfile):

        utils.run_script('''
        # Tabix expects the header line to start with a '#'
        ('{echo}' -n '#'; cat '{infile}') | '{bgzip}' > '{tmpfile}'
        '''.format(echo=echo, infile=infile, bgzip=bgzip, tmpfile=tmpfile))
        os.rename(tmpfile, outfile)
        utils.run_cmd([tabix, '-p', 'vcf', outfile])

    elif not os.path.exists(tbifile):
        utils.run_cmd([tabix, '-p', 'vcf', outfile])

    # print("{} -> {}".format(infile, outfile))

def get_conversions_to_do():
    for fname in os.listdir(augmented_pheno_dir):
        src_fname = os.path.join(augmented_pheno_dir, fname)
        dest_fname = os.path.join(augmented_pheno_gz_dir, fname)
        if not os.path.exists(dest_fname) or os.stat(src_fname).st_mtime > os.stat(dest_fname).st_mtime:
            yield src_fname

utils.mkdir_p(augmented_pheno_gz_dir)

infiles = list(get_conversions_to_do())
print('number of phenos to process:', len(infiles))
num_processes = multiprocessing.cpu_count() * 3//4 + 1
p = multiprocessing.Pool(num_processes)
p.map_async(convert, infiles).get(1e8) # Makes KeyboardInterrupt work