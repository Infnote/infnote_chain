#!/usr/bin/env bash

export PATH=/usr/local/bin:$PATH
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
pipenv install
pyinstaller main.spec -y
cp ./dist/main /usr/local/bin/ichain
ichain server restart
