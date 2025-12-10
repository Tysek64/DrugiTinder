# Altered DB module

Because there is already enough clutter in top-level directory bruv

## Purpose

This module exists solely for presentation purposes.
It is a standalone unit with code capable of (allegedly):

- generating and running the database from DDL script
- quickly deploying and rebuilding the database in docker
- populating the database
- upgrading the database to one compliant with the new schema
- hand-guide the user through the process
- for now that' it (for now it does nothing of the above)
^^ one day

## How to present

### First, build the docker image

```sh
docker build -t <image_name> .
```

I suggest using a git bash and running the deploy.sh, populate.sh and
migrate.sh to test it (necessary parameters should be in first lines of scripts)

However, if you do not want to do this, then proceed with this:

```sh
docker run -d --name <CONTAINER_NAME> -p <HOST_PORT>:5432 pdb-demo 
```

### populate it

Either use python populating script or a vibe-coded (my deepest apologies)
rust-based populating script (caveat: does not make subscriptions unique).
I modified the python script a little to use the environment variables, so run:
"

```sh
export DB_HOST=localhost
export DB_PORT="$HOST_PORT"
export DB_USER=kbd
export DB_PASS=kochamy_bazy_danych
export DB_NAME=pdb_demo
```

"
or any windows way of doing this.

#### then, to migrate

The correct migration script is "alter_db_2.sql"

```sh
cat <MIGRATION_FILE> | docker exec -i <CONTAINER_NAME> psql -U kbd -d pbd_demo
```
