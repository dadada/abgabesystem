# Programmieren [1,2] Gitlab

## Authentisierung

- use GITZ LDAP for login
- not allow "create new repo"

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

## (optional) sync script

- (one-way) sync students and groups from [Stud.IP REST API](http://docs.studip.de/develop/Entwickler/RESTAPI) to [Gitlab REST API](https://docs.gitlab.com/ce/api/)
- fork public repo with CI config etc into one private repo per student
- give students *Developer* access
- *Owner* is whoever
- group *tutors* has *Master* access to all repos (students sometimes switch groups)
- students *Request Access* to "Abgabepartner" repo, *tutors* can grant access
