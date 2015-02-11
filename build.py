import argparse
from collections import namedtuple
from pathlib import Path, PurePosixPath
import tempfile
from subprocess import check_call
from urllib.parse import urlparse
import os.path
import sys

Repo = namedtuple('Repo', 'url branch')

def sr(repo):
    return 'git://studentrobotics.org/{}.git'.format(repo)

REPOSITORIES = [
    Repo(sr('comp/ranker'), 'master'),
    Repo(sr('comp/srcomp'), 'master'),
    Repo(sr('comp/srcomp-http'), 'master'),
    Repo(sr('comp/srcomp-scorer'), 'master'),
    Repo(sr('tools'), 'new-tools'),
    Repo(sr('brain/herdsman'), 'master'),
    Repo('https://github.com/prophile/sr-scheduler-2015', 'master')
]

parser = argparse.ArgumentParser(description='SR Python distribution builder')
targets = parser.add_mutually_exclusive_group(required=True)
targets.add_argument('-o', '--output', help='directory to output built distributions',
                    type=Path)
targets.add_argument('-r', '--rsync', help='remote directory to output build distributions',
                    type=str)
parser.add_argument('-v', '--virtualenv', help='path to virtualenv',
                    default='/usr/bin/virtualenv')
args = parser.parse_args()

root_deps = ['wheel',
             'nose',
             'Sphinx==1.3b2']

def create_virtualenv(directory, python=sys.executable):
    check_call((args.virtualenv, '-p', python, directory))

with tempfile.TemporaryDirectory() as tmpdir:
    work = Path(tmpdir).resolve()
    if args.output is not None:
        DST = args.output.resolve()
    else:
        DST = work / 'dist'
        DST.mkdir()
    virtenv = work / 'venv'
    print('Creating virtualenv...')
    create_virtualenv(str(virtenv))
    for root_dep in root_deps:
        check_call([str(virtenv / 'bin/pip'),
                    'install',
                    root_dep])
    for repo in REPOSITORIES:
        name = PurePosixPath(urlparse(repo.url).path).stem
        check_call(['git', 'clone', '-b', repo.branch, repo.url, name],
                   cwd=str(work))
        check_call([str(virtenv / 'bin/python'),
                    'setup.py',
                    'sdist',
                    '-d',
                    str(DST)],
                   cwd=str(work / name))
        check_call([str(virtenv / 'bin/python'),
                    'setup.py',
                    'bdist_wheel',
                    '-d',
                    str(DST)],
                   cwd=str(work / name))
    if args.rsync is not None:
        print('Copying to target...')
        check_call(['rsync', '--recursive', str(DST) + '/', args.rsync])

