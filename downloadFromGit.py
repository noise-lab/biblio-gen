#!/usr/bin/env python
# Copyright 2013, Sam Burnett. See LICENSE for licensing info.
#
# This script:
# 1. Clones a git repository containing a bunch of bib files and a biblio-gen
# configuration file.
# 2. Concatenates the bib files to create a master bibliography file. This lets
# your organize your bib files into directories and files. For example, by
# conference and year.
# 3. Symlinks files from the static/ directory into the output directory tree
# (specified by the OUTPUT_DIR configuration variable.) It only symlinks file
# which don't already exist.

import errno
import os
import shutil
import subprocess
import sys
import traceback

import BibTeX
import config

def update_repository(remote_repository, local_repository):
    if not os.path.isdir(local_repository):
        code = subprocess.call(['git', 'clone', remote_repository, local_repository])
        if code != 0:
            print >>sys.stderr, 'Error cloning git repository'
            sys.exit(1)
    else:
        code = subprocess.call(['cd', local_repository, ';', 'git', 'pull', remote_repository], shell=True)
        if code != 0:
            print >>sys.stderr, 'Error pulling from remote git repository'
            sys.exit(1)

def index_bib_files_in_directory(output_handle, dirname, basenames):
    for basename in basenames:
        if os.path.splitext(basename)[1] != '.bib':
            continue
        filename = os.path.join(dirname, basename)
        print 'Checking', filename

        try:
            BibTeX.parseFile(filename)
        except:
            traceback.print_exc()
            print 'Skipping', filename, 'because of errors'
            continue

        with open(filename) as input_handle:
            for line in input_handle:
                output_handle.write(line)

def write_master_bib_file(local_repository):
    if os.path.isabs(config.MASTER_BIB):
        print >>sys.stderr, 'MASTER_BIB must not be an absolute path! It is currently', config.MASTER_BIB
    bib_path = os.path.join(local_repository, config.MASTER_BIB)
    with open(bib_path, 'w') as handle:
        os.path.walk(local_repository, index_bib_files_in_directory, handle)

def symlink_missing_files(output_dir, dirname, basenames):
    dest_dir = os.path.join(output_dir, os.path.relpath(dirname, 'static'))
    try:
        print 'mkdir', dest_dir
        os.makedirs(dest_dir)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

    for basename in basenames:
        dest_filename = os.path.join(dest_dir, basename)
        if os.path.exists(dest_filename):
            print 'Skipping', dest_filename
            continue
        filename = os.path.abspath(os.path.join(dirname, basename))
        if not os.path.isfile(filename):
            continue
        print 'symlink', filename, 'to', dest_filename
        os.symlink(filename, dest_filename)

def symlink_missing_resources(local_repository):
    template_file = os.path.normpath(os.path.join(local_repository, config.TEMPLATE_FILE))
    if not os.path.isfile(template_file):
        print 'Symlinking _template_.html to %s' % (template_file,)
        os.symlink(os.path.abspath('_template_.html'), template_file)
    bibtex_template_file = os.path.normpath(os.path.join(local_repository, config.BIBTEX_TEMPLATE_FILE))
    if not os.path.isfile(bibtex_template_file):
        print 'Symlinking _template_bibtex.html to %s', (bibtex_template_file,)
        os.symlink(os.path.abspath('_template_bibtex.html'), bibtex_template_file)

    output_dir = os.path.join(local_repository, config.OUTPUT_DIR)
    os.path.walk('static', symlink_missing_files, output_dir)

def main():
    if len(sys.argv) < 2:
        print >>sys.stderr, "Usage: %s <git repository> [local directory] [bibliography.cfg]"
        sys.exit(1)

    remote_repository = sys.argv[1]
    local_repository = os.path.basename(remote_repository)
    base, ext = os.path.splitext(local_repository)
    if ext == '.git':
        local_repository = os.path.join('repositories', base)
    if len(sys.argv) >= 3:
        local_repository = sys.argv[2]
    config_name = 'bibliography.cfg'
    if len(sys.argv) >= 4:
        config_name = sys.argv[3]

    update_repository(remote_repository, local_repository)

    config_path = os.path.join(local_repository, config_name)
    config.load(config_path)

    write_master_bib_file(local_repository)
    symlink_missing_resources(local_repository)

if __name__ == '__main__':
    main()
