# The abgabesystem

[GitHub](https://github.com/timschubert/abgabesystem)

## About

*Behold, the (almighty) abgabesystem!*

The aim of this project is to automate the handling of students' homework solutions using Gitlab.
So far It can

- import student accounts from LDAP,
- import a list of users from Stud.IP,
- create groups for courses in Gitlab,
- set up repositories for the students
- run automated style-checks and
- test for plagiarisms.

## Setup Gitlab and CI runners

There are multiple components involved in the abgabesystem.
The CI script uses a [Docker Container](https://github.com/timschubert/docker-abgabesystem) that contains the Python module and the [JPlag](https://jplag.ipd.kit.edu/) plagiarism checker.
Another container with [Checkstyle](https://github.com/timschubert/docker-checkstyle) is optionally required for style checking of each student repository.

If you do not already have a working Gitlab instance see [here](https://docs.gitlab.com/omnibus/README.html#installation) how to install and configure it.
Additionally you will need the [Gitlab CI runner](https://docs.gitlab.com/runner/).
For performance reasons, you might want to have the CI runner on another host than Gitlab or otherwise limit the resources available to the runner (depending on the number of students and CI jobs).

See [here](https://docs.gitlab.com/ce/administration/auth/ldap.html#doc-nav) on how to configure LDAP authentication.

## Install the python module

Install the python module using

```
$ virtualenv abgabesystem
$ source abgabesystem/bin/activate
$ pip install .
```

## Set up the course

To proceed, you need to have an [API token](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html) with administrative privileges.
After having configured Gitlab and the runner, continue with setting up your course.
Gitlab can only add existing users to projects, so we create pseudo-users that later will be fetched from LDAP, the first time each user logs in.

First create your course either using the Gitlab UI or

```
$ abgabesystem courses -c <some_course>
```

Next, since there is currently no API available to export a list of participants from [https://www.studip.de/](Stud.IP), we use the CSV file (encoded as latin-1 🤢) that lists all students currently enrolled in the course.
This list may of course change from time to time, so make sure to re-run the script regularly.

```
$ abgabesystem users -c <course> -s <students.csv> -b <LDAP base domain> -p main
```

Now create a fork of this repository inside the namespace of the course.

This repository contains CI jobs that need their own [Docker Container](https://github.com/timschubert/docker-abgabesystem).
Build the container, push it to the container registry and create a new runner that uses the container.
You can also [automate this](https://docs.gitlab.com/ce/ci/docker/using_docker_build.html) using the CI scripts included in the Docker container projects and let your Gitlab CI build and deploy the updated containers for you.

Proceed by creating an API token that has access to the group of the course.
Add this token as `PRIVATE_API_TOKEN` to the [secret variables](https://docs.gitlab.com/ce/ci/variables/) of the forked abgabesystem project.
Then generate an SSH deploy key and add the private part as `SSH_PRIVATE_KEY` and the public key as `SSH_PUBLIC_KEY` to the secret variables.
The key will be used by the CI script to fetch from the student projects.

At last, you can add everyone with permission to view all student solutions to the group of the course.

## Checking student solutions

When you have reachd the deadline for an exercise, push a new tag to `<course>/abgabesystem` to trigger the plagiarism checker and automatically create a tag in each student project.

```
$ git tag <exercise_name>
$ git push --tags
```

Check the build artifacts of the CI job for the results of the plagiarism checker.
