#!/usr/bin/env bash
pwd
export PATH=/usr/local/bin:$PATH
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
pipenv install
pipenv run pyinstaller ./main.spec -y
cp ./dist/main /usr/local/bin/ichain
ichain server restart
