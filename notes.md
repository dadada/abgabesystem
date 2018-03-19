# Programmieren [1,2] Gitlab

- https://docs.gitlab.com/omnibus/README.html

## Authentication

- use GITZ LDAP for login
- not allow "create new repo"


## Structure

- main repo
  + publish example solutions
  + CI config for checkstyle
  + Protected Runner for JPlag
  + restrict access to branches with example solutions
   
- student repos
  + forked from main repo
  + one repo per student
  + student has *Developer* Access
  + *tutors* group has *Master* access
  + students can request access (Abgabepartner)
  + *tutors* can grant access

## Checkstyle

- GitLab CI
- [Docker](https://docs.gitlab.com/omnibus/docker/README.html)container
- [Shared Runner](https://docs.gitlab.com/ce/ci/runners/README.html)
- restrict Container to [checkstyle](http://checkstyle.sourceforge.net/)
- disable internet access for container
  
## JPlag

- Deadline [at,cron]job or schedule via gitlab
- triggers [Protected Runner](https://docs.gitlab.com/ee/ci/runners/README.html#protected-runners)
- creates automatic protected TAG in each repo
- checks out TAG from all repos into /tmp and runs [JPlag](https://jplag.ipd.kit.edu/)
- replace with MOSS? https://github.com/soachishti/moss.py
- deploy key in each repo

## (optional) sync script

- (one-way) sync students and groups from [Stud.IP REST API](http://docs.studip.de/develop/Entwickler/RESTAPI) to [Gitlab REST API](https://docs.gitlab.com/ce/api/)

# Replicate (TODO: ansible playbook)

- install gitlab
- install docker
- copy gitlab.rb
- partially protected
- default project limit = 0
- shared runner for checkstyle

- protected runner for
  
  + setting protected tags
  + running jplag

- script for creating repos and groups
