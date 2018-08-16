#!/usr/bin/env python3

import argparse
import gitlab
import logging as log
import csv
import secrets
import subprocess
import os


class Student():
    """A Gitlab user

    Students are read from the CSV file that was exported from Stud.IP.
    For each user, a dummy LDAP user is created in Gitlab.
    Upon the first login Gitlab fetches the complete user using LDAP.
    """

    def __init__(self, user, mail, name, group):
        self.user = user
        self.email = mail
        self.name = name
        self.group = group

    def from_csv(csvfile):
        """Creates an iterable containing the users"""
        reader = csv.DictReader(csvfile, delimiter=';', quotechar='"')

        for line in reader:
            yield Student(line['Nutzernamen'], line['E-Mail'], line['Vorname']
                          + ' ' + line['Nachname'], line['Gruppe'])


def create_tag(project, tag, ref):
    """Creates protected tag on ref

    The tag is used by the abgabesystem to mark the state of a solution at the
    deadline
    """

    print('Project %s. Creating tag %s' % (project.path, tag))

    project.tags.create({
        'tag_name': tag,
        'ref': ref
    })


def get_students(gl, students_csv):
    """Returns already existing GitLab users for students from provided CSV file that have an account.
    """

    for student in Student.from_csv(students_csv):
        users = gl.users.list(search=student.user)
        if len(users) > 0:
            yield users[0]


def create_user(gl, student, ldap_base, ldap_provider):
    """Creates a GitLab user account student.
    Requires admin privileges.
    """

    user = gl.users.create({
        'email': student.email,
        'username': student.user,
        'name': student.name,
        'provider': ldap_provider,
        'skip_confirmation': True,
        'extern_uid': 'uid=%s,%s' % (student.user, ldap_base),
        'password': secrets.token_urlsafe(nbytes=32)
    })
    user.customattributes.set('group', student.group)

    return user


def create_users(gl, args):
    with open(args.students, encoding='iso8859') as students_csv:
        for student in Student.from_csv(students_csv):
            try:
                create_user(gl, student, args.ldap_base, args.ldap_provider)
            except gitlab.exceptions.GitlabCreateError:
                log.warn('Failed to create user: %s' % student.user)


def fork_reference(gl, reference, namespace, deploy_key):
    """Create fork of solutions for student.
    """

    fork = reference.forks.create({
        'namespace': namespace.id
    })
    project = gl.projects.get(fork.id)
    project.visibility = 'private'
    project.container_registry_enabled = False
    project.lfs_enabled = False
    deploy_key = project.keys.create({
        'title': "Deploy Key",
        'key': deploy_key
    })
    project.keys.enable(deploy_key.id)
    project.save()

    return project


def create_project(gl, group, user, reference, deploy_key):
    """Creates a namespace (subgroup) and forks the project with
    the reference solutions into that namespace
    """

    subgroup = None

    try:
        subgroup = gl.groups.create({
            'name': user.username,
            'path': user.username,
            'parent_id': group.id
        })
    except gitlab.exceptions.GitlabError as e:
        subgroups = group.subgroups.list(search=user.username)
        if len(subgroups) > 0 and subgroup[0].name == user.username:
            subgroup = subgroups[0]
            subgroup = gl.groups.get(subgroup.id, lazy=True)
        else:
            raise(e)
    try:
        subgroup.members.create({
            'user_id': user.id,
            'access_level': gitlab.DEVELOPER_ACCESS,
        })
    except gitlab.exceptions.GitlabError:
        log.warning('Failed to add student %s to its own group' % user.username)

    try:
        fork_reference(gl, reference, subgroup, deploy_key)
    except gitlab.exceptions.GitlabCreateError as e:
        log.warning(e.error_message)


def setup_course(gl, group, students_csv, deploy_key):

    solution = None
    reference_project = None

    try:
        solution = gl.groups.create({
            'name': 'solutions',
            'path': 'solutions',
            'parent_id': group.id,
            'visibility': 'internal',
        })
    except gitlab.exceptions.GitlabCreateError as e:
        log.info('Failed to create solutions group. %s' % e.error_message)
        solutions = group.subgroups.list(search='solutions')
        if len(solutions) > 0 and solutions[0].name == 'solutions':
            solution = gl.groups.get(solutions[0].id, lazy=True)
        else:
            raise(gitlab.exceptions.GitlabCreateError(error_message='Failed to setup solutions subgroup'))

    try:
        reference_project = gl.projects.create({
            'name': 'solutions',
            'namespace_id': solution.id,
            'visibility': 'internal',
        })
        reference_project.commits.create({
            'branch': 'master',
            'commit_message': 'Initial commit',
            'actions': [
                {
                    'action': 'create',
                    'file_path': 'README.md',
                    'content': 'Example solutions go here',
                },
            ]
        })
    except gitlab.exceptions.GitlabCreateError as e:
        log.info('Failed to setup group structure. %s' % e.error_message)
        projects = solution.projects.list(search='solutions')
        if len(projects) > 0 and projects[0].name == 'solutions':
            reference_project = gl.projects.get(projects[0].id)
        else:
            raise(gitlab.exceptions.GitlabCreateError(error_message='Failed to setup reference solutions'))

    if solution is None or reference_project is None:
        raise(gitlab.exceptions.GitlabCreateError(error_message='Failed to setup course'))

    for user in get_students(gl, students_csv):
        create_project(gl, solution, user, reference_project, deploy_key)


def projects(gl, args):
    groups = gl.groups.list(search=args.course)
    if len(groups) == 0 and groups[0].name == args.course:
        log.warn('This group does not exist')
    else:
        group = groups[0]
        with open(args.deploy_key, 'r') as key, open(args.students, encoding='iso8859') as students_csv:
            key = key.read()
            setup_course(gl, group, students_csv, key)


def deadline(gl, args):
    """Checks deadlines for course and triggers deadline if it is reached"""

    deadline_name = args.tag_name
    try:
        reference = gl.projects.get(args.reference, lazy=True)

        for fork in reference.forks.list():
            project = gl.projects.get(fork.id, lazy=False)
            try:
                create_tag(project, deadline_name, 'master')
            except gitlab.exceptions.GitlabCreateError as e:
                print(e.error_message)

    except gitlab.exceptions.GitlabGetError as e:
        print(e.error_message)


def plagiates(gl, args):
    """Runs the plagiarism checker (JPlag) for the solutions with a certain tag
    """

    tag = args.tag_name
    reference = gl.projects.get(args.reference, lazy=True)
    try:
        os.mkdir('solutions')
    except os.FileExistsError as e:
        print(e)
    os.chdir('solutions')

    for fork in reference.forks.list():
        project = gl.projects.get(fork.id, lazy=True)
        try:
            subprocess.run(
                ['git', 'clone', '--branch', tag, project.ssh_url_to_repo, project.path_with_namespace])
            os.chdir('..')
        except:
            print(e.error_message)

    subprocess.run(
        ['java', '-jar', args.jplag_jar, '-s', 'solutions', '-p', 'java', '-r', 'results', '-bc', args.reference, '-l', 'java17'])


def course(gl, args):
    try:
        group = gl.groups.create({
            'name': args.course,
            'path': args.course,
            'visibility': 'internal',
        })
        log.info('Created group %s' % args.course)
    except gitlab.exceptions.GitlabCreateError as e:
        log.warning('Failed to create group %s. %s' % (args.course, e.error_message))


if __name__ == '__main__':

    gl = gitlab.Gitlab.from_config()
    gl.auth()
    log.info('authenticated')

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='subcommands')

    user_parser = subparsers.add_parser(
        'users',
        help='Creates users from LDAP')
    user_parser.set_defaults(func=create_users)
    user_parser.add_argument('-s', '--students', dest='students')
    user_parser.add_argument('-b', '--ldap-base', dest='ldap_base')
    user_parser.add_argument('-p', '--ldap-provider', dest='ldap_provider')

    course_parser = subparsers.add_parser(
        'courses',
        help='Create course')
    course_parser.set_defaults(func=course)
    course_parser.add_argument('-c', '--course', dest='course')

    projects_parser = subparsers.add_parser(
        'projects',
        help='Setup projects')
    projects_parser.set_defaults(func=projects)
    projects_parser.add_argument('-c', '--course', dest='course')
    projects_parser.add_argument('-d', '--deploy-key', dest='deploy_key')
    projects_parser.add_argument('-s', '--students', dest='students')

    deadline_parser = subparsers.add_parser(
        'deadline',
        description='set tags at deadline')
    deadline_parser.set_defaults(func=deadline)
    deadline_parser.add_argument('-t', '--tag-name', dest='tag_name')
    deadline_parser.add_argument('-r', '--reference', dest='reference')

    plagiates_parser = subparsers.add_parser(
        'plagiates',
        description='set tags at plagiates')
    plagiates_parser.set_defaults(func=plagiates)
    plagiates_parser.add_argument('-t', '--tag-name', dest='tag_name')
    plagiates_parser.add_argument('-r', '--reference', dest='reference')
    plagiates_parser.add_argument('-j', '--jplag-jar', dest='jplag_jar')

    args = parser.parse_args()

    log.basicConfig(filename='example.log', filemode='w', level=log.DEBUG)

    if 'func' in args:
        args.func(gl, args)
    else:
        parser.print_help()
