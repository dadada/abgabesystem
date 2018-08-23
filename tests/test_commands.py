import gitlab

from abgabesystem.commands import create_users, projects, deadline, plagiates, course


gl = gitlab.Gitlab.from_config()
gl.auth()


def test_create_users():
    pass


def test_courses():
    pass


def test_projects():
    pass


def test_deadlines():
    pass


def test_plagiates():
    pass
