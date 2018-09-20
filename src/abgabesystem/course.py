import logging as log


class InvalidCourse(Exception):
    pass


def create_subgroup(gl, name, parent_group):
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
    group = gl.groups.create({
        "name": course_name,
        "path": course_name.lower().replace(" ", "_"),
        "visibility": "internal",
    })
    log.info("Created group %s" % course_name)
    create_students_group(gl, group)
    create_solutions_group(gl, group)

    return group
