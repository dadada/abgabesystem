import csv
import argparse
import gitlab

from mimetypes import guess_type


gl = gitlab.Gitlab.from_config()
gl.auth()


def group_name(longname):
    """Use the group number (located at start of group name)"""

    if longname in ['keine Teilnahme an den Übungen', 'keiner Funktion oder Gruppe zugeordnet', 'Gruppe']:
        return None
    else:
        return longname.split(' ')[0]


def parse_groups_csv(csvfile, encoding='utf-8'):
    """Reads the names of the groups from CSV file and yields the group names
    """

    with open(csvfile, 'r', encoding=encoding) as lines:
        """ Get distinct values from first column (groups)"""

        reader = csv.reader(lines, delimiter=';', quotechar='"')
        zipped = list(zip(*reader))

        for groupname in set(zipped[0]):
            short_name = group_name(groupname)

            """Discard groups that are None"""
            if short_name:
                yield(short_name)


def parse_users_csv(csvfile, encoding='utf-8'):
    """Reads user information from a CSV file and yields id and group"""

    with open(csvfile, 'r', encoding=encoding) as lines:
        reader = csv.DictReader(lines, delimiter=';', quotechar='"')

        for line in reader:
            yield line['Nutzernamen'], group_name(line['Gruppe'])


def create_student(user_id, email, tutorial):
    """Create user and add to tutorial group and workgroup based on preferred Abgabepartner
    User will later be updated with password from LDAP

    https://gitlab.com/gitlab-org/gitlab-ee/issues/699
    """
    pass


def create_abgabegruppe(tutorial):
    """Create a Abgabegruppe"""
    pass


def create_tutorial(course, group):
    """Creates a group via Gitlab API"""

    # this is the short path, not the full path
    path = group.replace(' ', '_').lower()

    try:
        subgroup = gl.groups.create({'name': group, 'path': path, 'parent_id': course.id})
        return subgroup
    except gitlab.exceptions.GitlabHttpError as e:
        print(e)


def create_course(course_name):

    courses = gl.groups.list(search=course_name)
    course = None

    if len(courses) == 0:
        path = course_name.replace(' ', '_').lower()
        course = gl.groups.create({'name': course_name, 'path': path})
    else:
        course = courses[0]

    return course


def create_course_admin_group(course):
    """Creates an administrative group for the course
    This group will be added as owner of each student repo"""

    try:
        subgroup = gl.groups.create({'name': 'admin', 'path': 'admin', 'parent_id': course.id})
        return subgroup
    except gitlab.exceptions.GitlabHttpError as e:
        print(e)

"""TODO
- create admin group for course and add hiwis

- add users (LDAP) with custom attribute for group, matrikelnummer
  + if user exists set custom attributes

- add users to course

- create student repos
  + fork from common repo
  + add admin group to each repo as owner / master


- create search for custom attribute (-> checkout repos for group)

"""

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Import groups and users from data source')
    parser.add_argument('course', type=str, nargs=1, help='name of the course')
    parser.add_argument('source', type=str, nargs=1, help='data source')
    parser.add_argument('--encoding', type=str, nargs=1, help='encoding of source')

    args = parser.parse_args()

    type, _ = guess_type(args.source[0])
    course = args.course[0]

    print(type)

    if type == 'text/csv':

        course = create_course(course)
        admins = create_course_admin_group(course)
        # TODO get functions from API and add hiwis to admins
        #users = parse_users_csv(args.source[0], args.encoding[0])

    elif type == None:

        print('MIME type not recognized')
