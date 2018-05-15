#!/usr/bin/env python3

import argparse
import yaml
import gitlab
import logging as log
import csv
import secrets
import subprocess
import os


class Course(yaml.YAMLObject):
    """A course"""

    yaml_tag = 'Course'

    def __init__(self, name, base, plagiates, deadlines, studentsfile):
        self.name = name
        self.base = base
        self.plagiates = plagiates
        self.deadlines = deadlines
        self.students = studentsfile

    def sync_group(self, gl):
        found = gl.groups.list(search=self.name)
        print(found)

        if len(found) > 0:
            for g in found:
                if g.name == self.name:
                    log.info('Found existing group %s' % found[0].name)
                    return g

        path = self.name.replace(' ', '_').lower()
        log.info('%s: Creating group' % self.name)
        group = gl.groups.create({
            'name': self.name,
            'path': path,
            'visibility': 'internal'
        })
        return group

    def sync_base(self, gl):
        found = self.group.projects.list(search=self.base)
        if len(found) == 0:
            self.base = gl.projects.create({
                'name': self.base,
                'namespace_id': self.group.id,
                'visibility': 'internal'
            })
            log.info('%s: Created project base repo' % self.name)
            data = {
                'branch': 'master',
                'commit_message': 'Initial commit',
                'actions': [
                    {
                        'action': 'create',
                        'file_path': 'README.md',
                        'content': 'README'
                    }
                ]
            }
            self.base.commits.create(data)

    def sync_projects(self, gl):
        self.sync_base(gl)


class Student():
    """A student"""

    def __init__(self, user, mail, name, group):
        self.user = user
        self.email = mail
        self.name = name
        self.group = group

    def from_csv(csvfile):
        reader = csv.DictReader(csvfile, delimiter=';', quotechar='"')

        for line in reader:
            yield Student(line['Nutzernamen'], line['E-Mail'], line['Vorname']
                          + ' ' + line['Nachname'], line['Gruppe'])

    def sync_user(self, gl, ldap):
        """Creates a dummy user for users that do not exist in gitlab
        but in LDAP and have not logged in yet"""

        found = gl.users.list(search=self.user)
        user = None
        if len(found) > 0:
            user = found[0]
        else:
            log.info('Creating student %s' % self.user)
            user = gl.users.create({
                'email': self.email,
                'username': self.user,
                'name': self.name,
                'provider': ldap['provider'],
                'skip_confirmation': True,
                'extern_uid': 'uid=%s,%s' % (self.user, ldap['basedn']),
                'password': secrets.token_urlsafe(nbytes=32)
            })
        # TODO create groups for abgabegruppen
        # group is stored in custom attribute
        # https://docs.gitlab.com/ee/api/custom_attributes.html
        user.customattributes.set('group', self.group)

        return user


def sync_project(gl, course, student):
    """Create user projects as forks from course/solutions in namespace of
    course and add user as developer (NOT master) user should not be able
    to modify protected TAG or force-push on protected branch users can
    later invite other users into their projects"""

    # tmp TODO
    #for project in student.user.projects.list():
    #    gl.projects.delete(project.id)

    projects = course.group.projects.list(search=student.user.username)
    project = None
    if len(projects) == 0:
        base = course.group.projects.list(search=course.base)[0]
        base = gl.projects.get(base.id)

        log.info('Creating project %s' % student.user.username)
        fork = base.forks.create({
            'namespace': student.user.username,
            'name': student.user.username
        })
        project = gl.projects.get(fork.id)
        project.path = student.user.username
        project.name = student.user.username
        project.visibility = 'private'
        project.save()
        course.group.transfer_project(to_project_id=fork.id)
    else:
        project = gl.projects.get(id=projects[0].id)

    try:
        student_member = project.members.get(student.user.id)
        student_member.access_level = gitlab.DEVELOPER_ACCESS 
        student_member.save()
    except gitlab.exceptions.GitlabGetError as e:
        student_member = project.members.create({'user_id': student.user.id, 'access_level':
                                                 gitlab.DEVELOPER_ACCESS})
    project.keys.create({'title': 'abgabesystem', 'key': open('abgabesystem.key.pub').read()})
    project.container_registry_enabled = False
    project.lfs_enabled = False
    project.save()


def create_tag(project, tag, ref):
    """Create protected tag on ref"""

    print('Project %s. Creating tag %s' % (project.name, tag))

    project.tags.create({
        'tag_name': tag,
        'ref': ref
    })


def sync(gl, conf, args):
    """Sync groups and students from Stud.IP to Gitlab and create student
    projects

    one-way sync!!!
    """

    course = conf['course']
    print(course.name)
    course.group = course.sync_group(gl)
    course.sync_base(gl)

    with open(course.students, encoding='latin1') as csvfile:
        for student in Student.from_csv(csvfile):
            try:
                student.user = student.sync_user(gl, conf['ldap'])
                print("%s %s" % (student.user.username, student.user.name))
                sync_project(gl, course, student)
            except gitlab.exceptions.GitlabCreateError as e:
                log.warn(e)


def list_projects(gl, conf, args):
    groups = gl.groups.list(search=conf['course'].name)
    print(groups)
    if len(groups) == 0:
        pass
    for g in groups:
        if (g.name == args.course):
            for project in g.projects.list(all=True):
                project = gl.projects.get(project.id)
                print(project.ssh_url_to_repo)


def get_base_project(gl, conf, args):
    return conf['course']['base']


def deadline(gl, conf, args):
    """Checks deadlines for course and triggers deadline if it is reached"""

    deadline_name = args.tag_name
    course = conf['course']
    group = gl.groups.list(search=course.name)[0]
    course.group = gl.groups.get(group.id)
    for project in course.group.projects.list(all=True):
        project = gl.projects.get(project.id)
        print(project.name)
        try:
            create_tag(project, deadline_name, 'master')
        except gitlab.exceptions.GitlabCreateError as e:
            print(e)


def plagiates(gl, conf, args):
    groups = gl.groups.list(search=conf['course'].name)
    tag = args.tag_name
    print(groups)
    if len(groups) == 0:
        pass
    for g in groups:
        if g.name == conf['course'].name:
            try:
                os.mkdir('repos')
            except os.FileExistsError as e:
                print(e)
            os.chdir('repos')
            for project in g.projects.list(all=True):
                project = gl.projects.get(project.id)
                try:
                    subprocess.run(
                        ['git', 'clone', '--branch', tag, project.ssh_url_to_repo])
                except subprocess.CalledProcessError as e:
                    print(e)

            os.chdir('..')
            subprocess.run(
                ['java', '-jar', '/app/jplag.jar', '-s', 'repos', '-p', 'java', '-r', 'results', '-bc', '$BASECODE', '-l', 'java18'])


def parseconf(conf):
    """Reads course from config file"""

    with open(args.config[0], 'r') as conf:
        return yaml.load(conf)


if __name__ == '__main__':

    gl = gitlab.Gitlab.from_config()
    gl.auth()
    log.info('authenticated')

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config', type=str, nargs=1, help='path to config file',
        default=['config.yml'])
    subparsers = parser.add_subparsers(title='subcommands')

    sync_parser = subparsers.add_parser(
        'sync',
        help='students and courses from Stud.IP and LDAP')
    sync_parser.set_defaults(func=sync)

    projects_parser = subparsers.add_parser(
        'projects',
        description='list projects for course')
    projects_parser.set_defaults(func=list_projects)
    projects_parser.add_argument('course')

    deadline_parser = subparsers.add_parser(
        'deadline',
        description='set tags at deadline')
    deadline_parser.set_defaults(func=deadline)
    deadline_parser.add_argument('tag_name')

    plagiates_parser = subparsers.add_parser(
        'plagiates',
        description='set tags at plagiates')
    plagiates_parser.set_defaults(func=plagiates)
    plagiates_parser.add_argument('tag_name')

    args = parser.parse_args()
    conf = parseconf(args.config)

    log.basicConfig(filename='example.log', filemode='w', level=log.DEBUG)

    if 'func' in args:
        args.func(gl, conf, args)
    else:
        parser.print_help()
