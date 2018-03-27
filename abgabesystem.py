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

    def tag(self, project):
        """Create protected tag on ref for all deadlines that have been
        reached"""

        try:
            project.tags.create({
                'tag_name': self.tag,
                'ref': self.ref
            })
        except gitlab.exceptions.GitlabHttpError as e:
            log.warn(e)


class Course(yaml.YAMLObject):
    """A course"""

    yaml_tag = 'Course'

    def setup_gitlab_group(self, groups):
        try:
            found = groups.list(search=self.name)
            return found[0]
        except gitlab.exceptions.GitlabHttpError as e:
            log.info(e)
            if e.response_code == 404:
                gl.groups.create({})
                path = self.name.replace(' ', '_').lower()
                group =  gl.groups.create({
                    'name': self.name,
                    'path': path
                })
                for repo in self.repos:
                    group.repos.create({
                        'name': repo,
                        'namespace_id': group.path,
                        'visibility': 'internal'
                    })
                return group
            else:
                raise e

    def __init__(self, name, deadlines, repos):
        self.name = name
        self.repos = repos
        self.deadlines = deadlines

    def projects(self, groups):
        return groups.list(search=self.name)[0].projects.list()


class Student():
    """A student"""

    def __init__(self, user, mail, name, group):
        self.user = user
        self.email = mail
        self.name = name
        self.group = group

    def setup_project(self, base, course):
        """Create user projects as forks from course/solutions in namespace of
        course and add user as developer (NOT master) user should not be able
        to modify protected TAG or force-push on protected branch users can
        later invite other users into their projects"""

        fork = course.group.projects.list(name=self.user)
        if len(fork) == 0:
            fork = base.forks.create({
                'name': self.user,
                'namespace': base.namspace,
                'visibility': 'private'
            })

        fork.members.create({
            'user_id': self.user,
            'access_level': gitlab.DEVELOPER_ACCESS
        })

        return fork

    def setup_ldap_dummy(self, users, provider, basedn):
        # TODO call from creation of student object()

        """Creates a dummy user for users that do not exist in gitlab
        but in LDAP and have not logged in yet"""

        users = users.list(search=self.user)

        if len(users) == 0:
            dummy = users.create({
                'email': self.email,
                'username': self.name,
                'name': self.user,
                'provider': provider,
                'skip_confirmation': True,
                'extern_uid': 'uid=%s,%s' % (self.user, basedn),
                'password': secrets.token_urlsafe(nbytes=32)
            })

            return dummy
        else:
            return users[0]

    def from_csv(csvfile):
        reader = csv.DictReader(csvfile, delimiter=';', quotechar='"')

        for line in reader:
            student = Student(line['Nutzernamen'],
                              line['E-Mail'],
                              line['Vorname'] + ' ' + line['Nachname'],
                              line['Gruppe'])
            yield student


def create_students(gl, conf, args):
    with open(args.students[0], 'r') as csvfile:
        for student in Student.from_csv(csvfile):
            student.setup_ldap_dummy(gl.users, conf['ldap']['provider'], conf['ldap']['basedn'])
            student.setup_project('solutions', args['course'][0]) #TODO
            print(student)


def create_courses(gl, conf, args):
    for course in conf['courses']:
        course.setup_gitlab_group(gl.groups)
        print(course)


def create_deadlines(gl, conf, args):
    for course in conf['courses']:
        for deadline in course.deadlines:
            pass
            #if deadline.time <= datetime.datetime.now():
                # deadline has approached
                # TODO setup cronjob?
                # deadline.tag(project)


if __name__ == '__main__':

    gl = gitlab.Gitlab.from_config()
    gl.auth()

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, nargs=1, help='path to config file', default='config.yml')

    course_parser = parser.add_subparsers('courses')
    course_parser.set_defaults(func=create_courses)

    student_parser = parser.add_subparsers('students')
    student_parser.add_argument('students', desc='Exported CSV file from Stud.IP', nargs=1, type=str)
    student_parser.add_argument('course', desc='Course for CSV file', nargs=1, type=str)
    student_parser.set_defaults(func=create_students)

    deadline_parser = parser.add_subparsers('deadlines')
    deadline_parser.set_defaults(func=create_deadlines)

    args = parser.parse_args()

    with open(args.config, 'r') as conf:
        conf = yaml.safe_load(conf)
        args.func(gl, conf, args)
