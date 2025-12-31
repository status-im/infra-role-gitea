# Backups

There's two folders that need to be backed up:

* `/docker/gitea/backup` - Postgres DB [database dump](https://www.postgresql.org/docs/current/app-pgdump.html).
* `/docker/gitea/app/data/git` - Git repositories (excluding `.ssh` subdirectories).

The database dumps are done with a [systemd timer](https://www.freedesktop.org/software/systemd/man/systemd.timer.html) on a daily basis:
```bash
mburcul@node-01.he-eu-fsn1.ci.gitea:/docker/gitea %  s list-timers -a | grep dump      
Thu 2026-01-01 00:00:00 UTC 15h left            Wed 2025-12-31 00:00:00 UTC 8h ago              dump-gitea-db.timer                  dump-gitea-db.service
```
and then backed up with [Restic](https://github.com/status-im/infra-role-restic-backups), as are the `app/data/git` folders:
```bash
mburcul@node-01.he-eu-fsn1.ci.gitea:/docker/gitea %  s list-timers -a | grep backup-gitea
Thu 2026-01-01 01:00:00 UTC 16h left            Wed 2025-12-31 01:00:00 UTC 7h ago              backup-gitea-db.timer                backup-gitea-db.service
Thu 2026-01-01 02:00:00 UTC 17h left            Wed 2025-12-31 02:00:00 UTC 6h ago              backup-gitea-repos.timer             backup-gitea-repos.service
```

# Restoring

## Backup Existing Data

Create a copy of Gitea folder:
```bash
cd /docker/gitea
docker compose down
cd ../
sudo cp -r gitea gitea_bkp
```

## Restore Backup

### DB

To restore DB backup to the same directory the destination permissions need to be changed:
```bash
sudo chmod g+w -R /docker/gitea/backup
sudo chmod o+w -R /docker/gitea/app/data/git/
```
Restore the latest backup for db:
```bash
sudo -i -u restic restic restore --target=/ b1e51df5
sudo -i -u restic restic restore --target=/ 44ef3fa2
```

```bash
mburcul@node-01.he-eu-fsn1.ci.gitea:/docker/gitea % sudo -i -u restic restic restore --target=/ b1e51df5
repository 44ade15c opened (version 2, compression level auto)
[0:00] 100.00%  10 / 10 index files loaded
restoring snapshot b1e51df5 of [/docker/gitea/db/backup] at 2025-12-31 01:00:00.128000743 +0000 UTC by restic@node-01.he-eu-fsn1.ci.gitea to /
Summary: Restored 5 files/dirs (0 B) in 0:00, skipped 112 files/dirs 25.732 MiB
```

### Gitea app
:warning: This is a destructive operation, especially when done using an older backup.

Remove old data (required because restic user cannot overwrite files owned by uid 101000):
```bash
sudo rm -rf /docker/gitea/app/data/git/*
```
Restore the latest backup for the Gitea app
```bash
sudo -i -u restic restic restore --target=/ 44ef3fa2
```
Fix ownership for Gitea container (expects uid/gid 101000):
```bash
sudo chown -R 101000:101000 /docker/gitea/app/data/git
```

By using `--target=/` we restore the backup to the same location from which it was copied.

## Load Database Dump

:warning: This is a destructive operation, especially when done using an older backup.

Purge the DB to make sure restore really works:
```bash
sudo rm -fr /docker/gitea/db/data/*
docker compose up -d db
sleep 15s
docker compose exec db pg_restore \
  -U gitea \
  -d gitea \
  -v \
  --jobs=4 \
  /backup/gitea
```
Start the Gitea App as well:
```bash
docker compose up -d
```
