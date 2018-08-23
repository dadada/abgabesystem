import os
import subprocess
import subprocess

from .students import Student, create_user, get_students
from .projects import create_tag, setup_course
from gitlab.exceptions import GitlabCreateError, GitlabGetError


def create_users(gl, args):
    """Creates Gitlab users from exported students list
    """
    with open(args.students, encoding='iso8859') as students_csv:
        for student in Student.from_csv(students_csv):
            try:
                create_user(gl, student, args.ldap_base, args.ldap_provider)
            except GitlabCreateError:
                log.warn('Failed to create user: %s' % student.user)


def projects(gl, args):
    """Creates the projects for all course participants
    """
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

        try:
            create_tag(reference, deadline_name, 'master')
        except GitlabCreateError as e:
            print(e.error_message)

        for fork in reference.forks.list():
            project = gl.projects.get(fork.id, lazy=False)
            try:
                create_tag(project, deadline_name, 'master')
            except GitlabCreateError as e:
                print(e.error_message)

    except GitlabGetError as e:
        print(e.error_message)


def plagiates(gl, args):
    """Runs the plagiarism checker (JPlag) for the solutions with a certain tag
    """

    tag = args.tag_name
    reference = gl.projects.get(args.reference, lazy=False)
    if not os.path.exists('solutions'):
        os.mkdir('input')
    os.chdir('input')
    try:
        subprocess.run(
            ['git', 'clone', '--branch', tag, reference.ssh_url_to_repo, reference.path_with_namespace])
    except subprocess.CalledProcessError as e:
        print(e.error_message)
    for fork in reference.forks.list():
        project = gl.projects.get(fork.id, lazy=False)
        try:
            subprocess.run(
                ['git', 'clone', '--branch', tag, project.ssh_url_to_repo, project.path_with_namespace])
        except subprocess.CalledProcessError as e:
            print(e.error_message)
    os.chdir('..')
    subprocess.run(
        ['java', '-jar', args.jplag_jar, '-s', input, '-p', 'java', '-r', 'results', '-bc', args.reference, '-l', 'java17'])


def course(gl, args):
    """Creates the group for the course
    """
    try:
        group = gl.groups.create({
            'name': args.course,
            'path': args.course,
            'visibility': 'internal',
        })
        log.info('Created group %s' % args.course)
    except GitlabCreateError as e:
        log.warning('Failed to create group %s. %s' % (args.course, e.error_message))
