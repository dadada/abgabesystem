import gitlab


def auth(config="/tmp/python-gitlab.cfg"):
    gl = gitlab.Gitlab.from_config(config_files=[config])
    gl.auth()

    return gl
