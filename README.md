# Description

This role configures an instance of [Gitea](https://gitea.io/) using Docker Compose.

# Configuration

```yaml
gitea_app_name: 'Example.org Repos'
gitea_app_web_domain: 'gitea.example.org'
gitea_app_ssh_domain: 'git.example.org'
gitea_app_ssh_port: 22
gitea_app_secret_key: 'super-secret-key'
gitea_app_log_level: 'debug'

# DB
gitea_db_pass: 'super-secret-db-pass'

# Admin
gitea_app_admin_user: 'root'
gitea_app_admin_pass: 'secret-root-pass'
gitea_app_admin_email: 'root@example.org'
```

## Initialisation

Organization can be initialised  with:
```yaml
gitea_organizations:
  - org1
  - org2
```
# Administration

You can manage the services using Docker Compose:
```
 > docker-compose ps
  Name                 Command               State                           Ports                         
-----------------------------------------------------------------------------------------------------------
gitea-app   /usr/bin/entrypoint /bin/s ...   Up      22/tcp, 0.0.0.0:2222->2222/tcp, 0.0.0.0:3000->3000/tcp
gitea-db    docker-entrypoint.sh postgres    Up      0.0.0.0:5432->5432/tcp  
```
For example you can easily re-create containers:
```
 > docker-compose up --force-recreate -d
Recreating gitea-db ... done
Recreating gitea-app ... done
```

# Backups

A Systemd timer creates `pg_dump` backups of the PostgreSQL database daily:
```
 > sudo systemctl list-timers -a dump-gitea-db
NEXT                        LEFT    LAST PASSED UNIT                ACTIVATES            
Sat 2021-03-20 00:00:00 UTC 9h left n/a  n/a    dump-gitea-db.timer dump-gitea-db.service
```
