import csv


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

