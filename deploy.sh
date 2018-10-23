#!/usr/bin/env bash

# copy file to server
for server in ${SERVER_LIST}
do
scp -oStrictHostKeyChecking=no -i ./ichain.pem ichain.tgz root@${server}:~/
ssh -oStrictHostKeyChecking=no -t -i ./ichain.pem root@${server} "
ichain server stop
tar -xzf ichain.tgz
rm ichain.tgz
cp dist/main /usr/local/bin/ichain
ichain server start -f
rm -r dist
"
done
