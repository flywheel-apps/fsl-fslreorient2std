#!/usr/bin/env python

import os
import re
import csv
import json
import string
import logging
import datetime
from pprint import pprint

logging.basicConfig()
log = logging.getLogger('fslreorient2std')


def _write_metadata(nifti_file_name, classification):
    """
    Extracts metadata from input nifti file and writes to .metadata.json.
    """
    import json

    # Build metadata
    metadata = {}

    # File metadata
    nifti_file = {}
    nifti_file['name'] = os.path.basename(nifti_file_name)
    nifti_file['classification'] = classification

    # Append the nifti_file to the files array
    metadata['acquisition'] = {}
    metadata['acquisition']['files'] = [nifti_file]

    # Write out the metadata to file (.metadata.json)
    metafile_outname = os.path.join('/flywheel/v0/output','.metadata.json')
    with open(metafile_outname, 'w') as metafile:
        json.dump(metadata, metafile)

    # Show the metadata
    if os.path.exists(metafile_outname):
        log.info(' Generated %s' % metafile_outname)
        pprint(metadata)
    else:
        log.info(' Failure! metadata file was not generated!')

    return metafile_outname


if __name__ == '__main__':
    """
    Extracts metadata from input nifti file and writes to .metadata.json.
    """
    import json
    import shlex
    import subprocess

    log.setLevel(getattr(logging, 'DEBUG'))
    logging.getLogger('fslreorient2std').setLevel(logging.INFO)
    log.info(' Start: %s' % datetime.datetime.utcnow())

    # Grab Config
    CONFIG_FILE_PATH = '/flywheel/v0/config.json'
    with open(CONFIG_FILE_PATH) as config_file:
        config = json.load(config_file)

    nifti_file_path = config['inputs']['nifti']['location']['path']
    nifti_file_name = config['inputs']['nifti']['location']['name']
    output_name = config['config']['output_name'] if config['config'].has_key('output_name') else ''
    classification = config['inputs']['nifti']['object']['classification']

    # Set output name
    OUTDIR = '/flywheel/v0/output'
    output_basename = output_name.split('.nii')[0] + '.nii.gz' if output_name else nifti_file_name.split('.nii')[0] + '_std.nii.gz'
    output_name = os.path.join(OUTDIR, output_basename)

    # File name hackery to deal with the fact that fslreorient2std can't handle spaces in filenames
    temp_input_name = os.path.join(os.path.dirname(nifti_file_path), 'input.nii' + nifti_file_name.split('.nii')[-1] )
    temp_output_name = os.path.join(OUTDIR, 'output.nii' + nifti_file_name.split('.nii')[-1])
    log.info(' Temp moving %s -> %s' % (nifti_file_path, temp_input_name))
    os.rename(nifti_file_path, temp_input_name)

    # Run Command
    cmd = shlex.split('fsl5.0-fslreorient2std  \"%s\" \"%s\" ' %  (temp_input_name, temp_output_name))
    log.info(' Running command: %s' % cmd)
    status = subprocess.call(cmd)

    if status:
        log.info(' Errors encountered running fslreorient2std! Exit Status=1')
        os.sys.exit(1)
    else:
        log.info(' Success!')
        # Rename input/output files after run
        log.info(' Moving %s -> %s' % (temp_input_name, nifti_file_path))
        os.rename(temp_input_name, nifti_file_path)
        log.info(' Moving %s -> %s' % (temp_output_name, output_name))
        os.rename(temp_output_name, output_name)

    metadatafile = _write_metadata(output_name, classification)

    log.info(' Complete: %s' % datetime.datetime.utcnow())
    os.sys.exit(0)
