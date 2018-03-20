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
    """Reads user information from a CSV file and yields each user as a dict"""

    with open(csvfile, 'r', encoding=encoding) as lines:
        reader = csv.DictReader(lines, delimiter=';', quotechar='"')

        for line in reader:
            yield line['Nutzernamen'], line['E-Mail'], group_name(line['Gruppe'])


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

    path = group.replace(' ', '_').lower()

    # TODO implement create subgroups method in python-gitlab for API v4
    subgroup = course.subgroups.create({'name': group, 'path': path})


def create_course(course_name):

    try:
        path = course_name.replace(' ', '_').lower()
        course = gl.groups.create({'name': course_name, 'path': path})
    except:
        # TODO implement search method in python-gitlab for API v4
        course = gl.groups.get(id=34)

    return course


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
        print(course)

        groupnames = parse_groups_csv(args.source[0], args.encoding[0])
        for group in groupnames:
            create_tutorial(course, group)

        users = parse_users_csv(args.source[0], args.encoding[0])


    elif type == None:

        print('MIME type not recognized')
