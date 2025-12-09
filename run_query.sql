#!/bin/bash

docker exec pdb-test-run-rust psql -U kbd -d pdb_demo -c "$1"
