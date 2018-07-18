# The abgabesystem

## Setup

0. Optional: If you have not previously set up GitLab for the abgabesystem, you can use the playbook in playbook.yml to setup your instance.

1. Create a new group with the name of the course.

2. Create a fork of abgabesystem inside that group.

3. Configure config.yml and generate an SSH key pair.
   Add the private key to the fork as the secret variable SSH_PRIVATE_KEY.
   Add the public key to config.yml as deploy_key.

4. Export the student list from StudIP and add it to the project.

5. Create an API key with admin access and add it to the fork as the secret variable PRIVATE_API_TOKEN.

6. Add all administrative users to the group of your course (but not the students).

The CI jobs should then create the student repositories.

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
