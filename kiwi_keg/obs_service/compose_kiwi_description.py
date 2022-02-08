# Copyright (c) 2021 SUSE Software Solutions Germany GmbH. All rights reserved.
#
# This file is part of keg.
#
# keg is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# keg is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with keg. If not, see <http://www.gnu.org/licenses/>
#
"""
Usage:
    compose_kiwi_description --git-recipes=<git_clone_source> ... --image-source=<path> --outdir=<obs_out>
        [--git-branch=<name>] ...
        [--disable-version-bump]
        [--disable-update-changelog]
        [--disable-update-revisions]
    compose_kiwi_description -h | --help
    compose_kiwi_description --version

Options:
    --git-recipes=<git_clone_source>
        Remote git repository containing keg-recipes (multiples allowed).

    --git-branch=<name>
        Recipes repository branch to check out (multiples allowed, optional).

    --image-source=<path>
        Keg path in git source pointing to the image description.
        The path must be relative to the images/ directory.

    --outdir=<obs_out>
        Output directory to store data produced by the service.
        At the time the service is called through the OBS API
        this option is set.

    --disable-version-bump
        Do not increment the patch version number.

    --disable-update-changelog
        Do not update 'changes.yaml'.

    --disable-update-revisions
        Do not update '_keg_revisions'.
"""
import glob
import docopt
import itertools
import logging
import os
import shutil
import sys

from kiwi.xml_description import XMLDescription
from kiwi.utils.temporary import Temporary
from kiwi.command import Command
from kiwi.path import Path
from kiwi_keg.version import __version__
from kiwi_keg.image_definition import KegImageDefinition
from kiwi_keg.generator import KegGenerator
from kiwi_keg.source_info_generator import SourceInfoGenerator


log = logging.getLogger('compose_keg_description')


def get_kiwi_data(kiwi_config):
    description = XMLDescription(kiwi_config)
    return description.load()


def get_head_commit_hash(repo_path):
    result = Command.run(['git', '-C', repo_path, 'show', '--no-patch', '--format=%H', 'HEAD'])
    return result.output.strip('\n')


def get_image_version(kiwi_config):
    # It is expected that the <version> setting exists only once
    # in a keg generated image description. KIWI allows for profiled
    # <preferences> which in theory also allows to distribute the
    # <version> information between several <preferences> sections
    # but this would be in general questionable and should not be
    # be done any case by keg managed recipes. Thus the following
    # code takes the first version setting it can find and takes
    # it as the only version information available
    for preferences in get_kiwi_data(kiwi_config).get_preferences():
        image_version = preferences.get_version()
        if image_version:
            return image_version[0]
    if not image_version:
        sys.exit('Cannot determine image version.')


def get_revision_args(repo_dirs):
    rev_args = []
    if os.path.exists('_keg_revisions'):
        with open('_keg_revisions') as inf:
            for line in inf.readlines():
                rev_spec = line.strip('\n').split(' ')
                if len(rev_spec) != 2:
                    sys.exit('Malformed revision spec "{}".'.format(line.strip('\n')))
                repo_path = repo_dirs.get(rev_spec[0])
                if not repo_path:
                    log.warning('Warning: Cannot map URL "{}" to repository.'.format(rev_spec[0]))
                else:
                    rev_args += ['-r', '{}:{}..'.format(repo_path.name, rev_spec[1])]
    else:
        log.warning(
            'Warning: no _keg_revision file. '
            'Change file will contain all applicable commit messages.'
        )
    return rev_args


def generate_changelog(source_log, outdir, prefix, image_version, rev_args):
    prefix += '.' if prefix else ''
    changes_new = os.path.join(outdir, '{}changes.yaml.tmp'.format(prefix))
    changes_old = '{}changes.yaml'.format(prefix)
    Command.run([
        'generate_recipes_changelog',
        '-o', changes_new,
        '-f', 'yaml',
        '-t', image_version,
        *rev_args,
        source_log
    ])
    if os.path.exists(changes_old):
        with open(changes_new, 'a') as outf, open(changes_old) as inf:
            outf.write(inf.read())
    shutil.move(changes_new, os.path.join(outdir, changes_old))


def update_revisions(repo_dirs, outdir):
    with open(os.path.join(outdir, '_keg_revisions'), 'w') as outf:
        for rname, rpath in repo_dirs.items():
            chash = get_head_commit_hash(rpath.name)
            print('{} {}'.format(rname, chash), file=outf)


def main() -> None:
    args = docopt.docopt(__doc__, version=__version__)

    if not os.path.exists(args['--outdir']):
        Path.create(args['--outdir'])

    if len(args['--git-branch']) > len(args['--git-recipes']):
        sys.exit('Number of --git-branch arguments must not exceed number of git repos.')

    handle_changelog = not args['--disable-update-changelog']

    repo_dirs = {}
    for repo, branch in itertools.zip_longest(args['--git-recipes'], args['--git-branch']):
        temp_git_dir = Temporary(prefix='keg_recipes.').new_dir()
        if branch:
            Command.run(['git', 'clone', '-b', branch, repo, temp_git_dir.name])
        else:
            Command.run(['git', 'clone', repo, temp_git_dir.name])
        repo_dirs[repo] = temp_git_dir

    image_version = None
    old_kiwi_config = None
    if os.path.exists('config.kiwi'):
        old_kiwi_config = 'config.kiwi'

    if not args['--disable-version-bump'] and old_kiwi_config:
        # if old config.kiwi exists, increment patch version number
        version = get_image_version(old_kiwi_config)
        if version:
            ver_elements = version.split('.')
            ver_elements[2] = f'{int(ver_elements[2]) + 1}'
            image_version = '.'.join(ver_elements)

    image_definition = KegImageDefinition(
        image_name=args['--image-source'],
        recipes_roots=[x.name for x in repo_dirs.values()],
        track_sources=handle_changelog,
        image_version=image_version
    )
    image_generator = KegGenerator(
        image_definition=image_definition,
        dest_dir=args['--outdir']
    )
    image_generator.create_kiwi_description(
        overwrite=True
    )
    image_generator.create_custom_scripts(
        overwrite=True
    )
    image_generator.create_overlays(
        disable_root_tar=False, overwrite=True
    )

    if handle_changelog:
        sig = SourceInfoGenerator(image_definition, dest_dir=args['--outdir'])
        sig.write_source_info()
        rev_args = get_revision_args(repo_dirs)

        if not image_version:
            if old_kiwi_config:
                log.warning(
                    'Warning: generating changes file but version bump is disabled. '
                    'Using old version.'
                )
            image_version = get_image_version(os.path.join(args['--outdir'], 'config.kiwi'))

        for source_log in glob.glob(os.path.join(args['--outdir'], 'log_sources*')):
            flavor = source_log[len(os.path.join(args['--outdir'], 'log_sources')) + 1:]
            generate_changelog(source_log, args['--outdir'], flavor, image_version, rev_args)
            # clean up source log
            os.remove(source_log)

    if not args['--disable-update-revisions']:
        # capture current commits
        update_revisions(repo_dirs, args['--outdir'])
