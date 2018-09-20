# The abgabesystem

## Setup

Operations 1 and 2 require super user privileges to the API. The rest don't.

1. Import the students participating in the course into Gitlab. This is required to assign projects to each student. If you have exported a list of groups and functions from Stud.IP you can use that.
```
# abgabesystem users -s <students.csv> -b <LDAP base domain> -p main
```

2. Create a group for your course using
```
# abgabesystem courses -c <some_course>
   ```
   
3. Create a fork of this project inside the namespace of the group that has been created and configure your API token (`PRIVATE_API_TOKEN`) and deploy key (`SSH_PRIVATE_KEY`) (see .gitlab-ci.yml) for the forked project.

4. Set up the project for the example solutions and the student projects. If you have pre-existing example solutions place them in `<some_course>/solutions/solutions`.
```
# abgabesystem projects -c <some_course> -d <deploy key>
```

5. Add all administrative users (e.g. users supervising the course or checking homework solutions) to the group of the course.

6. At the deadline of each exercise trigger the plagiarism checker using
```
# git tag <exercise_name>
# git push --tags
```
It can be useful to do this from a cronjob.

## Recommended settings for gitlab.rb

```
 gitlab_rails['gitlab_default_can_create_group'] = false

 # see gitlab documentation and add your ldap config
 gitlab_rails['ldap_enabled'] = true
```

Also, you should 

- set the default project limit for each user to 0
- set default settings for projects to partially protected so that developers (e.g. students) can not force push tags and commits to protected branches (master) which is important for plagiarism controls.

## Workflow

To trigger the deadline of an exercise (e.g. Sunday at 15:00), push a tag (e.g.
ex1) to the cloned abgabesystem project.
The abgabesystem's CI job creates a tag of this name inside each student's project and then creates a checkout of each project's repository and runs [JPlag](https://github.com/jplag/jplag) to check for plagiates.
The results can be found inside the job artifacts.
The results are saved for each tag and can be downloaded as an archive.
