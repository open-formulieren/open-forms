#!/usr/bin/env python3
# bootstrap.py
# Bootstrap and setup a virtualenv with the specified requirements.txt
import argparse
import os
import stat
import sys
from shutil import move
from subprocess import call
from tempfile import mkstemp

description = """
Set up my development environment for me!
"""

project_name = 'openforms'

parser = argparse.ArgumentParser(description=description)
parser.add_argument('target', choices=['production', 'staging', 'test', 'jenkins', 'dev'],
                    help='production/staging/test/jenkins/dev')
parser.add_argument('--project', default=project_name,
                    help='Name of the project in your src directory, "%s" by default' % project_name)
parser.add_argument('--init', action='store_true',
                    help='Initialize a fresh "startproject" by pinning the requirements using pip-tools compile. '
                         'Automatically done if requirements/base.txt does not yet exist.')
parser.add_argument('--env', default='env',
                    help='Directory name for virtualenv, "env" by default')

args = parser.parse_args()


def replace_or_append(file_path, search_val, replace_val):
    file_handle, abs_path = mkstemp()
    new_file = open(abs_path, 'w')
    old_file = open(file_path, 'r')
    found = False
    for line in old_file:
        if line.startswith(search_val):
            new_file.write(replace_val)
            found = True
        else:
            new_file.write(line)
    if not found:
        new_file.write("\n" + replace_val)
    new_file.close()
    os.close(file_handle)
    old_file.close()
    os.remove(file_path)
    move(abs_path, file_path)
    os.chmod(file_path, 436)


def replace_wsgi_settings(target):
    path = os.path.join('src', project_name, 'wsgi.py')
    replace_or_append(
        path, 'os.environ.setdefault',
        'os.environ.setdefault("DJANGO_SETTINGS_MODULE", "%s.conf.%s")\n' % (project_name, target)
    )


def replace_manage_settings(target):
    path = os.path.join('src', project_name, 'manage.py')
    replace_or_append(
        path, '    os.environ.setdefault',
        '    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "%s.conf.%s")\n' % (project_name, target)
    )


def append_settings_activate(project, target, env):
    if os.name == 'posix':
        path = '%s/bin/activate' % env
        replace_or_append(path, 'export DJANGO_SETTINGS_MODULE=',
                          'export DJANGO_SETTINGS_MODULE=\'%s.conf.%s\'\n' %
                          (project, target))
    elif os.name == 'nt':
        path = '%s\\Scripts\\activate.bat' % env
        replace_or_append(path, 'set DJANGO_SETTINGS_MODULE=',
                          'set DJANGO_SETTINGS_MODULE=%s.conf.%s\n' %
                          (project, target))
        path = '%s\\Scripts\\deactivate.bat' % env
        replace_or_append(path, 'set DJANGO_SETTINGS_MODULE=',
                          'set DJANGO_SETTINGS_MODULE=\n')


def pip_compile_pin_requirements(virtualenv):
    print('\n== Compiling base requirements ==\n')
    if os.name == 'posix':
        pip_path = os.path.join(virtualenv, 'bin', 'pip')
    elif os.name == 'nt':
        pip_path = os.path.join(virtualenv, 'Scripts', 'pip')
    cmd_tpl = '{pip} install pip-tools'.format(pip=pip_path)
    call(cmd_tpl, shell=True)
    print('Error: Run `. env/bin/activate && ./bin/compile_dependencies.sh` to ensure you have requirements/base.txt and requirements/dev.txt')
    print('After that rerun bootstrap.py')
    sys.exit(1)

def main():
    virtualenv = args.env
    if not hasattr(sys, 'real_prefix'):
        print('\n== Creating virtual environment ==\n')
        call('virtualenv {0} --python=python3 --prompt="({1}-{2}) "'.format(
            virtualenv, args.project, args.target
        ), shell=True)
    print('\n== Set "%s.conf.%s" as default settings ==\n' % (args.project, args.target))
    append_settings_activate(args.project, args.target, args.env)

    if os.name == 'posix':
        # Make manage.py executable
        st = os.stat('src/manage.py')
        os.chmod('src/manage.py', st.st_mode | stat.S_IEXEC)
        django_admin_symlink = os.path.join(virtualenv, 'bin', 'django')
        if not os.path.exists(django_admin_symlink):
            os.symlink('../../src/manage.py', django_admin_symlink)

    print('\n== Upgrading Pip ==\n')
    if os.name == 'posix':
        pip_path = os.path.join(virtualenv, 'bin', 'pip')
    elif os.name == 'nt':
        pip_path = os.path.join(virtualenv, 'Scripts', 'pip')
    cmd_tpl = '{pip} install --upgrade pip'.format(pip=pip_path)
    call(cmd_tpl, shell=True)

    if args.init \
       or not os.path.exists(os.path.join('requirements', 'base.txt')) \
       or not os.path.exists(os.path.join('requirements', 'dev.txt')):
        pip_compile_pin_requirements(virtualenv)

    print('\n== Installing %s requirements ==\n' % args.target)
    if os.name == 'posix':
        os.environ['TMPDIR'] = '/var/tmp/'
        pip_path = os.path.join(virtualenv, 'bin', 'pip')
        cmd_tpl = '{pip} install -r requirements/{target}.txt'
    elif os.name == 'nt':
        pip_path = os.path.join(virtualenv, 'Scripts', 'pip')
        cmd_tpl = '{pip} install -r requirements\\{target}.txt'
    return call(cmd_tpl.format(pip=pip_path, target=args.target), shell=True)

if __name__ == '__main__':
    sys.exit(main())
