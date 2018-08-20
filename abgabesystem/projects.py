from gitlab.exceptions import GitlabError, GitlabCreateError

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
    except GitlabError as e:
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
    except GitlabError:
        log.warning('Failed to add student %s to its own group' % user.username)

    try:
        fork_reference(gl, reference, subgroup, deploy_key)
    except GitlabCreateError as e:
        log.warning(e.error_message)


def setup_course(gl, group, students_csv, deploy_key):
    """Sets up the internal structure for the group for use with the course
    """
    solution = None
    reference_project = None

    try:
        solution = gl.groups.create({
            'name': 'solutions',
            'path': 'solutions',
            'parent_id': group.id,
            'visibility': 'internal',
        })
    except GitlabCreateError as e:
        log.info('Failed to create solutions group. %s' % e.error_message)
        solutions = group.subgroups.list(search='solutions')
        if len(solutions) > 0 and solutions[0].name == 'solutions':
            solution = gl.groups.get(solutions[0].id, lazy=True)
        else:
            raise(GitlabCreateError(error_message='Failed to setup solutions subgroup'))

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
    except GitlabCreateError as e:
        log.info('Failed to setup group structure. %s' % e.error_message)
        projects = solution.projects.list(search='solutions')
        if len(projects) > 0 and projects[0].name == 'solutions':
            reference_project = gl.projects.get(projects[0].id)
        else:
            raise(GitlabCreateError(error_message='Failed to setup reference solutions'))

    if solution is None or reference_project is None:
        raise(GitlabCreateError(error_message='Failed to setup course'))

    for user in get_students(gl, students_csv):
        create_project(gl, solution, user, reference_project, deploy_key)

