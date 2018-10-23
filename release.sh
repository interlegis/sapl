#/bin/bash

VERSION=`git describe --tags --abbrev=0`
LAST_DIGIT=`echo $VERSION | cut -f 3 -d '.'`
MAIN_REV=`echo $VERSION | cut -f 1,2 -d '.'`
NEXT_NUMBER=$(($LAST_DIGIT + 1))
NEXT_VERSION=$MAIN_REV'.'$NEXT_NUMBER


function bump_version {
    sed -e s/$VERSION/$NEXT_VERSION/g docker-compose.yml > tmp1
    mv tmp1 docker-compose.yml

    sed -e s/$VERSION/$NEXT_VERSION/g setup.py > tmp2
    mv tmp2 setup.py


    sed -e s/$VERSION/$NEXT_VERSION/g sapl/templates/base.html > tmp3
    mv tmp3 sapl/templates/base.html
}

function commit_and_push {
   echo "committing..."
   git add docker-compose.yml setup.py sapl/templates/base.html
   git commit -m "Release: $NEXT_VERSION"
   git tag $NEXT_VERSION

   echo "sending to github..."
   git push origin $NEXT_VERSION
   git push origin

   echo "done."
}

case "$1" in
    --dry-run)
        echo "Dry run"
        bump_version
        echo "done."
        echo "Run git checkout -- docker-compose.yml setup.py to undo the files"

        exit 0
        ;;
    --publish)
       echo "generating release"
       bump_version
       commit_and_push
esac

