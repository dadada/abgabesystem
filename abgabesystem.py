#!/usr/bin/env python3

import argparse
import yaml
import gitlab
import datetime
import logging as log
import csv
import secrets


class Deadline(yaml.YAMLObject):
    """A deadline"""

    yaml_tag = 'Deadline'

    def __init__(self, tag, time, ref):
        self.tag = tag
        self.time = time
        self.ref = ref

    def trigger(self, project):
        """Create protected tag on ref"""

        try:
            project.tags.create({
                'tag_name': self.tag,
                'ref': self.ref
            })
        except gitlab.exceptions.GitlabHttpError as e:
            log.warn(e)

    def test(self):
        return self.time <= datetime.datetime.now()


class Course(yaml.YAMLObject):
    """A course"""

    yaml_tag = 'Course'

    def __init__(self, name, base, deadlines):
        self.name = name
        self.base = base
        self.deadlines = deadlines

    def create_group(self, gl):
        path = self.name.replace(' ', '_').lower()
        self.group = gl.groups.create({
            'name': self.name,
            'path': path
        })
        return self.group


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

    def create_user(self, gl, ldap):
        """Creates a dummy user for users that do not exist in gitlab
        but in LDAP and have not logged in yet"""

        return gl.users.create({
            'email': self.email,
            'username': self.name,
            'name': self.user,
            'provider': ldap['provider'],
            'skip_confirmation': True,
            'extern_uid': 'uid=%s,%s' % (self.user, ldap['basedn']),
            'password': secrets.token_urlsafe(nbytes=32)
        })


def fork_project(gl, group, base, user):
    """Create user projects as forks from course/solutions in namespace of
    course and add user as developer (NOT master) user should not be able
    to modify protected TAG or force-push on protected branch users can
    later invite other users into their projects"""

    # fork course base project (e.g. solutions)
    fork = base.forks.create({
        'name': user['name'],
        'namespace': group.namspace,
        'visibility': 'private'
    })

    # add student as member of project
    fork.members.create({
        'user_id': user,
        'access_level': gitlab.DEVELOPER_ACCESS
    })

    return fork


def create_project(group, name):
    return group.projects.create({
        'name': name,
        'namespace_id': group.path,
        'visibility': 'internal'
    })


def deadlines(gl, course, args):
    """Checks deadlines for course and triggers deadline if it is reached"""

    for deadline in course.deadlines:
        if deadline.test():
            deadline.trigger(course)


def sync(gl, conf, args):
    """Sync groups and students from Stud.IP to Gitlab and create student
    projects

    one-way sync!!!
    """

    for course in conf['courses']:
        course.create_group(gl)
        create_project(course.group)

        with open(args.students[0]) as csvfile:
            for student in Student.from_csv(csvfile):
                student.create_user(gl, conf['ldap'])


def parseconf(conf):
    """Reads courses from config file"""

    with open(args.config, 'r') as conf:
        return yaml.safe_load(conf)


if __name__ == '__main__':

    gl = gitlab.Gitlab.from_config()
    gl.auth()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config', type=str, nargs=1, help='path to config file',
        default='config.yml')
    subparsers = parser.add_subparsers(title='subcommands')

    sync_parser = subparsers.add_parser(
        'sync',
        description='students and courses from Stud.IP and LDAP')
    sync_parser.set_defaults(func=sync)
    sync_parser.add_argument('--students', nargs=1,
                             description='Students CSV file')

    deadline_parser = subparsers.add_parser('deadlines',
                                            description='trigger deadlines')
    deadline_parser.set_defaults(func=deadlines)

    args = parser.parse_args()
    conf = parseconf(args.conf)

    args.func(gl, conf, args)
