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
cp -f ./dist/main /usr/local/bin/ichain
# start server
ichain server restart
