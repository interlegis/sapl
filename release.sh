#/bin/bash

##
## Versioning info: [major].[minor].[patch][-RC[num]], example: 3.1.159, 3.1.159-RC1
##

# TODO: verificar porque só pega versões superiores (3.1.200 ao invés de 3.1.200-RC9)
# VERSION=`git describe --tags --abbrev=0`

VERSION_PATTERN='([0-9]+)\.([0-9]+)\.([0-9]+)(-RC[0-9]+)?'

SED_AWKWARD_PATTERN="[0-9]+\.[0-9]+\.[0-9]+(-RC[0-9]+){0,1}"

LATEST_VERSION=$(git tag | egrep $VERSION_PATTERN | sort --version-sort | tail -1)
MAJOR_VERSION=$(echo $LATEST_VERSION | cut -d"-" -f1)
IS_RC=$(echo $LATEST_VERSION | egrep '(-RC)')
HAS_MAJOR=$(git tag | egrep $MAJOR_VERSION"$")

if [ -n "$HAS_MAJOR" ]; then
   LATEST_VERSION=$MAJOR_VERSION
fi

LAST_DIGIT=`echo $MAJOR_VERSION | cut -f 3 -d '.'`
MAIN_REV=`echo $MAJOR_VERSION | cut -f 1,2 -d '.'`
NEXT_NUMBER=$(($LAST_DIGIT + 1))
NEXT_VERSION=$MAIN_REV'.'$NEXT_NUMBER

FINAL_VERSION=

function change_files {

    echo "Atualizando de "$LATEST_VERSION" para "$FINAL_VERSION

    sed -E s/$LATEST_VERSION/$FINAL_VERSION/g docker-compose.yml > tmp1
    mv tmp1 docker-compose.yml

    sed -E s/$LATEST_VERSION/$FINAL_VERSION/g setup.py > tmp2
    mv tmp2 setup.py

    sed -E s/$LATEST_VERSION/$FINAL_VERSION/g sapl/templates/base.html > tmp3
    mv tmp3 sapl/templates/base.html

    sed -E s/$LATEST_VERSION/$FINAL_VERSION/g sapl/settings.py > tmp4
    mv tmp4 sapl/settings.py
}

function set_major_version {
    if [ -z "$IS_RC" ] || [ -n "$HAS_MAJOR" ]; then
        FINAL_VERSION=$NEXT_VERSION
    else
        FINAL_VERSION=$MAJOR_VERSION
    fi
}

function set_rc_version {
    IS_RC=$(echo $LATEST_VERSION | egrep '(-RC)')
    MAJOR_VER=$(echo $LATEST_VERSION | cut -d"-" -f1)
    HAS_MAJOR=$(git tag | egrep "$MAJOR_VER$")

    if [ -z "$IS_RC" ]; then
        NEXT_RC_VERSION=$NEXT_VERSION"-RC0"
    else
        LAST_RC_DIGIT=$(echo $LATEST_VERSION | rev | cut -d"-" -f1 | rev | sed s/RC//)
        NEXT_RC_NUMBER=$(($LAST_RC_DIGIT + 1))
        NEXT_RC_VERSION=$(echo $LATEST_VERSION | cut -d"-" -f1)'-RC'$NEXT_RC_NUMBER
    fi

    FINAL_VERSION=$NEXT_RC_VERSION
}

function commit_and_push {
   echo "committing..."
   git add docker-compose.yml setup.py sapl/settings.py sapl/templates/base.html
   git commit -m "Release: $NEXT_VERSION"
   git tag $FINAL_VERSION

   echo "sending to github..."
   git push origin
   git push origin $FINAL_VERSION

   echo "done."
}

case "$1" in
    --latest)
       echo $LATEST_VERSION
       exit 0
       ;;
    --major)
       set_major_version
       echo "generating major release: "$FINAL_VERSION
       git tag $FINAL_VERSION
       change_files
       # commit_and_push
       exit 0
       ;;
    --rc)
       set_rc_version
       echo "generating release candidate: "$FINAL_VERSION
       git tag $FINAL_VERSION
       change_files
       # commit_and_push
       exit 0
      ;;
    --undo)
       git tag -d $LATEST_VERSION
       exit 0
       ;;
    --top)
       git tag | sort --version-sort | tail "-$2"
       exit 0
       ;;

esac

