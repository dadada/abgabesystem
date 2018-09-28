import logging as log


class InvalidCourse(Exception):
    """Raised if the selected course is invalid.
    """

    pass


def create_subgroup(gl, name, parent_group):
    """Creates a group with `parent_group` as its parent.

    Args:
        gl: gitlab API object
        name: name of the group to be created
        parent_group: parent group of the created group
    """

    log.info("Creating subgroup %s in group %s" % (name, parent_group.name))
    return gl.groups.create({
        "name": name,
        "path": name,
        "parent_id": parent_group.id
    })


def create_students_group(gl, parent_group):
    return create_subgroup(gl, "students", parent_group)


def create_solutions_group(gl, parent_group):
    return create_subgroup(gl, "solutions", parent_group)


def create_course(gl, course_name):
    """Creates a complete course as required by the `abgabesystem` including
    the students and solutions groups.

    Args:
        gl: gitlab API object
        course_name: name of the course, may contain any characters from
                     [0-9,a-z,A-Z,_, ]
    """

    group = gl.groups.create({
        "name": course_name,
        "path": course_name.lower().replace(" ", "_"),
        "visibility": "internal",
    })
    log.info("Created group %s" % course_name)
    create_students_group(gl, group)
    create_solutions_group(gl, group)

    return group
