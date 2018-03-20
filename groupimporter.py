import csv
import argparse

from mimetypes import guess_type


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


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Import groups and users from data source')
    parser.add_argument('course', type=str, nargs=1, help='name of the course')
    parser.add_argument('source', type=str, nargs=1, help='data source')
    parser.add_argument('--encoding', type=str, nargs=1, help='encoding of source')

    args = parser.parse_args()

    type, _ = guess_type(args.source[0])

    print(type)

    if type == 'text/csv':

        groupnames = parse_groups_csv(args.source[0], args.encoding[0])

        for group in groupnames:
            print(args.course[0] + ' ' + group)

        users = parse_users_csv(args.source[0], args.encoding[0])

        for user in users:
            print(user)

    elif type == None:

        print('MIME type not recognized')
