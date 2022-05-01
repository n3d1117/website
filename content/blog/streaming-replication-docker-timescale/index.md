---
title: Enabling TimescaleDB Streaming Replication for PostgreSQL 13 with Docker
description: This post shows how to set up streaming replication for a PostgreSQL 13 database with TimescaleDB extension using Docker, in order to create a 1:1 replica of the primary database that is always in sync.
date: 2021-10-22T02:28:42.000Z
slug: wildfly-docker-timescale
tags: [replication, docker, timescaledb, postgresql, big data]
toc: true
math: false
---

{{< note variant="info" >}}
  This post shows how to set up **streaming replication** for a PostgreSQL 13 database with TimescaleDB extension using Docker, in order to create a 1:1 replica of the primary database always in sync.
{{< /note >}}

## Introduction
Part of my work at [Magenta](https://magentalab.it) was to investigate the possibility of having a 1:1 replica of [AirQino](https://www.airqino.it/en/)'s production database (which had more than **100M rows**, running PostgreSQL 13 and [Timescale](https://www.timescale.com)), possibly on a different server, and having them **in sync** all the time for performance tests, offloading heavy queries and availability (also check out my [other post](/blog/2021/11/continuous-aggregates-timescale/) on implementing *continuous aggregates* to make database queries run faster).

As it turns out, TimescaleDB does not support for logical replication (using libraries like [pglogical](https://github.com/2ndQuadrant/pglogical)), but it can handle replication using PostgreSQL's built-in [streaming replication](https://www.postgresql.org/docs/current/warm-standby.html#STREAMING-REPLICATION), which is what i ended up using. PostgreSQL achieves streaming replication by having replicas continuously stream the **WAL** (*Write-Ahead Logging*) from the primary database. For more information see PostgreSQL's [WAL Documentation](https://www.postgresql.org/docs/13/wal-intro.html)[^1].

## Preparing the primary database
1. Create a PostgreSQL user with a role that allows it to initialize streaming replication:
```sql
SET password_encryption = 'scram-sha-256'; 
CREATE ROLE repuser WITH REPLICATION PASSWORD 'SOME_SECURE_PASSWORD' LOGIN;
```
3. Add the following replication settings to `postgresql.conf` (which can be usually found in `$PGDATA` folder, i.e. `/var/lib/postgresql/data`):
```
listen_addresses= '*'
wal_level = replica
max_wal_senders = 2
max_replication_slots = 2
synchronous_commit = off
```
4. Add the following at the end of `$PGDATA/pg_hba.conf` to configure host-based authentication to accept connections from the replication user on the host of the replica:
```
host     replication     repuser   <REPLICA_IP>/32       scram-sha-256
```

5. Restart the primary database to apply changes
6. Finally, create a [replication slot](https://www.postgresql.org/docs/current/warm-standby.html#STREAMING-REPLICATION-SLOTS) and give it a name:

```sql
SELECT * FROM pg_create_physical_replication_slot('replica_1_slot');
```

## Configuring the replica

1. Stop Postgres instance:
```sh
pg_ctl -D $PGDATA -m fast -w stop
```

2. Clear `PGDATA` folder:

{{< note variant="warning" >}}
  **NOTE:** if you do this step while Postgres is running, you will get into trouble.
{{< /note >}}

```sh
rm -rf $PGDATA/*
```

3. Create a base backup on the replica:

{{< note variant="warning" >}}
**NOTE:** This may take a while, depending on the database size (less than 5 minutes for me).
You will also be asked to input the password interactively, the one you set up in step 1 of [preparing the primary database](#preparing-the-primary-database) section.
{{< /note >}}

```sh
pg_basebackup -h <PRIMARY_HOST> -p <PRIMARY_PORT> -D $PGDATA -U repuser -vP -R -W
```

4. Finally, restart Postgres instance:
```sh
pg_ctl -D $PGDATA -w start
```

## Automating it all using Docker Compose
Luckily, all these steps can be automated using Docker for a smooth setup. Timescale offers sample Docker configuration and run scripts with their [streaming-replication-docker](https://github.com/timescale/streaming-replication-docker) GitHub repository, which was very useful even though it is quite outdated (supports only up to PostgreSQL 10), so a few changes are needed.

### Primary setup
Create the following `PrimaryDockerfile`:
```dockerfile
FROM timescale/timescaledb:latest-pg13
ADD primary.sh /docker-entrypoint-initdb.d/
```

And then create the entrypoint script `primary.sh`:
```sh
# Create replica user
psql -U postgres -c "SET password_encryption = 'scram-sha-256';"
psql -U postgres -c "CREATE ROLE $REPLICA_USER WITH REPLICATION PASSWORD '$REPLICA_PASSWORD' LOGIN;"

# Add replication settings to primary postgres.conf
cat >> ${PGDATA}/postgresql.conf <<EOF
listen_addresses= '*'
wal_level = replica
max_wal_senders = 2
max_replication_slots = 2
synchronous_commit = off
EOF

# Add replication settings to primary pg_hba.conf
cat >> ${PGDATA}/pg_hba.conf <<EOF
host     replication     ${REPLICA_USER}   ${REPLICA_IP}/32       scram-sha-256
EOF

# Restart Postgres
pg_ctl -D ${PGDATA} -m fast -w restart

# Add replication slot
psql -U postgres -c "SELECT * FROM pg_create_physical_replication_slot('${REPLICA_NAME}_slot');"
```

This script will perform all the necessary steps to allow replication every time the database starts. If you plan on doing this without an entrypoint script (i.e. by running the commands directly with `docker exec`), make sure to run these as the `postgres` user by running `su - postgres` before issuing commands. By default, TimescaleDB image logs in as `root` user, which may break things.

### Replica setup
Please note that the replica setup involves shutting down the postgres instance and deleting contents of the `PGDATA` folder. As such, it must be executed from an entrypoint script and **not** while the container is running.

Create the following `ReplicaDockerfile`:
```dockerfile
FROM timescale/timescaledb:latest-pg13
ADD replica.sh /docker-entrypoint-initdb.d/
```
And then create the entrypoint script `replica.sh`:

```sh
echo "Stopping Postgres instance..."
pg_ctl -D ${PGDATA} -m fast -w stop

echo "Clearing PGDATA folder..."
rm -rf ${PGDATA}

echo "Creating base backup..."
PGPASSWORD=${REPLICATION_PASSWORD} pg_basebackup -h ${REPLICATION_HOST} -p ${REPLICATION_PORT} -D ${PGDATA} -U ${REPLICATION_USER} -vP -R -w

echo "Restarting Postgres instance..."
pg_ctl -D ${PGDATA} -w start
```

{{< note variant="warning" >}}
  **NOTE:** `pg_basebackup`'s `-W` option will ask for replication password interactively, which does not work well for automated setups. Instead, we can use the lowercase `-w` option and specify the password using the `PGPASSWORD` environment variable (or even using a `.pgpass` file). See [the docs](https://www.postgresql.org/docs/13/app-pgbasebackup.html) for more info.
{{< /note >}}

### Composing services
Finally, create a `docker-compose.yml` file:

{{< note variant="warning" >}}
  **NOTE:** for some reason, using the default `/var/lib/postgresql/data` as `PGDATA` for the replica didn't work for me: no matter how many times I stopped the Postgres instance, the `rm -rf ${PGDATA}` command always ended up throwing the error `rm: can't remove '/var/lib/postgresql/data': Resource busy`. Using a subfolder instead, such as `/var/lib/postgresql/data/pgdata`, ended up working fine.
{{< /note >}}

```yaml
version: '3'

services:
  
  # Primary DB
  primary:
    build:
        context: .
        dockerfile: PrimaryDockerfile
    environment:
        POSTGRES_USER: postgres
        POSTGRES_PASSWORD: postgres

        # Replication parameters
        REPLICA_NAME: replica_1
        REPLICA_USER: repuser
        REPLICA_PASSWORD: SOME_SECURE_PASSWORD
        REPLICA_IP: x.x.x.x # ip of the replica db
    ports:
        - 5432:5432
    volumes:
        - /var/primary-pg13-timescale/:/var/lib/postgresql/data
  
  # Replica DB
  replica:
    build:
        context: .
        dockerfile: ReplicaDockerfile
    environment:
        # Note: a replica is 1:1 of the production db, you cannot add new users/tables/views to it.
        # So these credentials are never really added (they're here to prevent initialization errors)
        POSTGRES_USER: dummy_user
        POSTGRES_PASSWORD: dummy_pw

        # Custom PDATA folder (for some reason the default `/var/lib/postgresql/data` doesn't work)
        PGDATA: /var/lib/postgresql/data/pgdata

        # Replication parameters
        REPLICA_USER: repuser
        REPLICATION_HOST: x.x.x.x # ip of the primary db
        REPLICATION_PORT: 5432
        REPLICATION_PASSWORD: SOME_SECURE_PASSWORD
    ports:
        - 5433:5432
    volumes:
        - /var/replica-pg13-timescale/:/var/lib/postgresql/data
```
And then run it with `docker-compose up`, you should see an output like this:

{{< img src="screenshot.png" caption="Example output of the `docker-compose up` command" w="800" >}}

## Conclusion
{{< note variant="success" >}}
  You should now have a fully working replica database always in sync with the primary one. Congrats! 🎉
{{< /note >}}

Keep in mind that it is read-only and there are a few limitations:
- Users and access roles are mirrored from the primary instance, which means you cannot use different credentials or add additional user to the replica only
- Tables and views cannot be created on the replica instance; you're basically only allowed to execute `SELECT` queries from it.

[^1]: TimescaleDB docs: [Replication and HA](https://docs.timescale.com/timescaledb/latest/how-to-guides/replication-and-ha/replication/).