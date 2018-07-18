# The Abgabesystem

## Setup

0. Configure gitlab with your LDAP configuration.

1.  Generate a deploy key and an API token.

2.  Set up container images and runners.
   - [checkstyle](https://ips1.ibr.cs.tu-bs.de/abgabesystem/checkstyle)
   - [abgabesystem](https://ips1.ibr.cs.tu-bs.de/abgabesystem/abgabesystem)

3.  Create a group for your course and add all administrative users to it.

4.  Clone [abgabesystem](https://ips1.ibr.cs.tu-bs.de/abgabesystem/docker-abgabesystem) as a private project of that group and add SSH_PRIVATE_KEY and PRIVATE_API_TOKEN to the private variables.

5.  Edit [config.yml](blob/master/config.yml) to include the name of the student list, your public
deploy key and the name of the course.

6.  Export student list from StudIP and add it to the project.

7.  wait for ci jobs to finish....

## Recommended settings for gitlab.rb

```
 gitlab_rails['gitlab_default_can_create_group'] = false
 gitlab_rails['gitlab_default_projects_features_container_registry'] = false

 # see gitlab documentation and add your ldap config
 gitlab_rails['ldap_enabled'] = true

 # if you don't have TLS otherwise
 letsencrypt['enable'] = true
```

Also, you should 

- set the default project limit for each user to 0 and
- set default settings for projects to partially protected so that developers (e.g. students) can not force push tag and commits to protected branches (master)

## Workflow

To trigger the deadline of an exercise (e.g. Sunday at 15:00), push a tag (e.g.
ex1) to the cloned abgabesystem project.
The abgabesystem's CI job creates a tag of this name inside each student's project and then creates a checkout of each project's repository and runs [JPlag](https://github.com/jplag/jplag) to check for plagiates.
The results can be found inside the job artifacts.
The results are saved for each tag and can be downloaded as an archive.
