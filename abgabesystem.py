#!/usr/bin/env python3

import argparse
import yaml
import gitlab
import datetime
import logging as log
import csv
import secrets
import time


class Deadline(yaml.YAMLObject):
    """A deadline"""

    yaml_tag = 'Deadline'

    def __init__(self, tag, time, ref):
        self.tag = tag
        self.time = time
        self.ref = ref

    def trigger(self, project):
        """Create protected tag on ref"""

        log.info('Creating tag %s' % self.tag)
        project.tags.create({
            'tag_name': self.tag,
            'ref': self.ref
        })

    def test(self):
        return self.time <= datetime.datetime.now()


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

    def sync_plagiates(self, gl):
        found = self.group.projects.list(search=self.plagiates)
        if len(found) == 0:
            self.base = gl.projects.create({
                'name': self.base,
                'namespace_id': self.group.id,
                'visibility': 'private'
            })
            log.info('%s: Created project plagiates repo' % self.name)

        projects = self.group.projects.list()
        """
        add all projects in group as submodules
        except plagiates itself
        """
        projects_list = ""

        for project in projects:
            if project.name != self.plagiates:
                projects_list += '../%s\n' % project.name

        data = {
            'branch': 'master',
            'commit_message': 'Add submodules',
            'actions': [
                {
                    'action': 'create',
                    'file_path': '.gitmodules',
                    'content': projects_list
                }
            ]
        }
        self.plagiates.commits.create(data)

    def sync_projects(self, gl):
        self.sync_base(gl)
        self.sync_plagiates(gl)


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

    print(student.user.name)
    projects = course.group.projects.list(search=student.user.name)
    if len(projects) > 0:
        print('found')
        return projects[0]

    base = course.group.projects.list(search=course.base)[0]
    base = gl.projects.get(base.id)

    log.info('Creating project %s' % student.user)
    fork = base.forks.create({
        'namespace': student.user.username,
        'name': student.name
    })
    project = gl.projects.get(fork.id)
    project.path = student.user.username
    project.name = student.name
    project.visibility = 'private'
    project.save()
    course.group.transfer_project(to_project_id=fork.id)
    student_member = project.members.get(student.user.id)
    student_member.access_level = gitlab.DEVELOPER_ACCESS 
    student_member.save()

    return project


def deadlines(gl, conf, args):
    """Checks deadlines for course and triggers deadline if it is reached"""

    for course in conf.courses:
        for deadline in course.deadlines:
            if deadline.test():
                for project in course.group.projects.list():
                    try:
                        deadline.trigger(project)
                    except gitlab.exceptions.GitlabHttpError as e:
                        log.warn(e)


def sync(gl, conf, args):
    """Sync groups and students from Stud.IP to Gitlab and create student
    projects

    one-way sync!!!
    """

    for course in conf['courses']:
        course.group = course.sync_group(gl)
        course.sync_base(gl)

        with open(course.students, encoding='latin1') as csvfile:
            for student in Student.from_csv(csvfile):

                print(course, student)
                try:
                    student.user = student.sync_user(gl, conf['ldap'])
                    sync_project(gl, course, student)
                except gitlab.exceptions.GitlabCreateError as e:
                    log.warn(e)

        course.sync_plagiates(gl)


def parseconf(conf):
    """Reads courses from config file"""

    with open(args.config, 'r') as conf:
        return yaml.load(conf)


if __name__ == '__main__':

    gl = gitlab.Gitlab.from_config()
    gl.auth()
    log.info('authenticated')

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config', type=str, nargs=1, help='path to config file',
        default='config.yml')
    subparsers = parser.add_subparsers(title='subcommands')

    sync_parser = subparsers.add_parser(
        'sync',
        help='students and courses from Stud.IP and LDAP')
    sync_parser.set_defaults(func=sync)

    deadline_parser = subparsers.add_parser('deadlines',
                                            description='trigger deadlines')
    deadline_parser.set_defaults(func=deadlines)

    args = parser.parse_args()
    conf = parseconf(args.config)

    log.basicConfig(filename='example.log', filemode='w', level=log.DEBUG)

    if 'func' in args:
        args.func(gl, conf, args)
    else:
        parser.print_help()
