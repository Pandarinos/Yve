#!/bin/bash

[ -f ./db/panda.sqlite3 ] && mv ./db/panda.sqlite3 ./db/panda.sqlite3.bak
sqlite3 ./db/panda.sqlite3 < ./db/create_panda_db.sql
[ -f ./db/panda.sqlite3 ] && echo "Done."
