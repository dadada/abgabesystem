# Programmieren [1,2] Gitlab

## Authentisierung

- use GITZ LDAP for login
- not allow "create new repo"

## Checkstyle

- GitLab CI
- (Docker)container
- Shared Runner
- restrict Container to checkstyle
- disable internet access for container
  
## Deadline [at,cron]job

- each repo has protected master branch -> used for handing in exercises
- create automatic protected TAG on deadline in each repo
- trigger via push to master repo
- start jplag via protected runner that can clone / checkout all repos

## (optional) sync script

- (one-way) sync students and groups from [Stud.IP REST API](http://docs.studip.de/develop/Entwickler/RESTAPI) to [Gitlab REST API](https://docs.gitlab.com/ce/api/)
- fork public repo with CI config etc into one private repo per student
- give students *Developer* access
- *Owner* is whoever
- group *tutors* has *Master* access to all repos (students sometimes switch groups)
- students *Request Access* to "Abgabepartner" repo, *tutors* can grant access
