#!/usr/bin/env bash

# install python environment in project path
export PIPENV_VENV_IN_PROJECT=1

# add bin path
export PATH=/usr/local/bin:$PATH

# avoid python3 setting problem
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# install packages
pipenv install
# generate executable file
pipenv run pyinstaller ./main.spec -y
# copy to global
scp -p "${SSH_SECRET}" -f ./dist/main root@47.254.197.123:/usr/local/bin/ichain
# start server
ssh -p "${SSH_SECRET}" root@47.254.197.123 ichain server restart
