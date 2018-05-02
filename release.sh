#/bin/bash

VERSION=`git describe --tags --abbrev=0`
LAST_DIGIT=`echo $VERSION | cut -f 3 -d '.'`
MAIN_REV=`echo $VERSION | cut -f 1,2 -d '.'`
NEXT_NUMBER=$(($LAST_DIGIT + 1))
NEXT_VERSION=$MAIN_REV'.'$NEXT_NUMBER

sed -e s/$VERSION/$NEXT_VERSION/g docker-compose.yml > tmp1
mv tmp1 docker-compose.yml

sed -e s/$VERSION/$NEXT_VERSION/g setup.py > tmp2
mv tmp2 setup.py

git add docker-compose.yml setup.py
git commit -m "Release: $NEXT_VERSION"
git tag $NEXT_VERSION
git push origin $NEXT_VERSION
git push origin
