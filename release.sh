#!/usr/bin/env bash

##
## Versioning info: [major].[minor].[patch][-RC[num]], example: 3.1.159, 3.1.159-RC1
##

## IMPORTANT: requires gh and git-extras commands installed
## Currently only runs on MacOS because of sed issue on lines 41 to 47 (see double quotes after -i)
##

# TODO: verificar porque só pega versões superiores (3.1.200 ao invés de 3.1.200-RC9)
# VERSION=`git describe --tags --abbrev=0`

VERSION_PATTERN='([0-9]+)\.([0-9]+)\.([0-9]+)(-RC[0-9]+)?'

SED_AWKWARD_PATTERN="[0-9]+\.[0-9]+\.[0-9]+(-RC[0-9]+){0,1}"

# Define colors
green_color='\033[0;32m'
red_color='\033[0;31m'
reset_color='\033[0m'

LATEST_VERSION=$(git tag | egrep $VERSION_PATTERN | sort --version-sort | tail -1)
MAJOR_VERSION=$(echo $LATEST_VERSION | cut -d"-" -f1)
MAJOR_TAG_CREATED=$(git tag | egrep $MAJOR_VERSION"$")

if [ -n "$MAJOR_TAG_CREATED" ]; then
   LATEST_VERSION=$MAJOR_VERSION
fi

IS_RC=$(echo $LATEST_VERSION | egrep '(-RC)')

LAST_DIGIT=`echo $MAJOR_VERSION | cut -f 3 -d '.'`
MAIN_REV=`echo $MAJOR_VERSION | cut -f 1,2 -d '.'`
NEXT_NUMBER=$(($LAST_DIGIT + 1))
NEXT_VERSION=$MAIN_REV'.'$NEXT_NUMBER

FINAL_VERSION=

function change_files {

    # TODO: figure out better way of getting latest version
    OLD_VERSION=$(grep -E 'interlegis/sapl:'$VERSION_PATTERN docker/docker-compose.yaml | cut -d':' -f3)

    echo "Updating from "$OLD_VERSION" to "$FINAL_VERSION""

    sed -E -i "" "s|$OLD_VERSION|$FINAL_VERSION|g" docker/docker-compose.yaml

    sed -E -i "" "s|$OLD_VERSION|$FINAL_VERSION|g" setup.py

    sed -E -i "" "s|$OLD_VERSION|$FINAL_VERSION|g" sapl/templates/base.html

    sed -E -i "" "s|$OLD_VERSION|$FINAL_VERSION|g" sapl/settings.py
}

function set_major_version {
    if [ -z "$IS_RC" ] || [ -n "$MAJOR_TAG_CREATED" ]; then
        FINAL_VERSION=$NEXT_VERSION
    else
        FINAL_VERSION=$MAJOR_VERSION
    fi
}

function set_rc_version {
    if [ -z "$IS_RC" ]; then
        NEXT_RC_VERSION=$NEXT_VERSION"-RC0"
    else
        LAST_RC_DIGIT=$(echo $LATEST_VERSION | rev | cut -d"-" -f1 | rev | sed s/RC//)
        NEXT_RC_NUMBER=$(($LAST_RC_DIGIT + 1))
        NEXT_RC_VERSION=$(echo $LATEST_VERSION | cut -d"-" -f1)'-RC'$NEXT_RC_NUMBER
    fi

    FINAL_VERSION=$NEXT_RC_VERSION
## DEBUG
#    echo "OLD_VERSION: $OLD_VERSION"
#    echo "FINAL_VERSION: $FINAL_VERSION"
}

# Function to display Yes/No prompt with colored message
prompt_yes_no() {
    while true; do
        echo -e "${green_color}$1 (y/n): ${reset_color}\c"
        read answer
        case $answer in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo -e "${red_color}Please answer 'yes' or 'no'.${reset_color}";;
        esac
    done
}

function commit_and_push {
   echo -e "${green_color}Committing new release $FINAL_VERSION...${color_reset}"
   git changelog --tag $FINAL_VERSION -x >> CHANGES.md
   git add docker/docker-compose.yaml setup.py sapl/settings.py sapl/templates/base.html CHANGES.md

   if prompt_yes_no "${green_color}Do you want to commit SAPL $FINAL_VERSION release locally?${reset_color}"; then
       git commit -m "Release: $FINAL_VERSION"
       git tag $FINAL_VERSION
       echo -e "${green_color}Commit and tag created locally!${color_reset}"
   else
       git reset --hard HEAD
       echo -e "${red_color}Aborting release creation!${color_reset}"
       return
   fi

   echo -e "${red_color}### BEFORE PROCEEDING, MAKE SURE THE NEW VERSION NUMBER AND CHANGES ARE CORRECT!${color_reset}"
   echo -e "${green_color}Release: $FINAL_VERSION${reset_color}"
   if prompt_yes_no "${green_color}Do you want to publish SAPL $FINAL_VERSION release on Github?${reset_color}"; then
      echo -e "${green_color}Publishing $FINAL_VERSION on Github...${reset_color}"
      current_date=$(date +%Y-%m-%d)
      git push origin 3.1.x
      gh release create $FINAL_VERSION --repo interlegis/sapl --title "Release: $FINAL_VERSION" --notes "Release notes for $FINAL_VERSION in CHANGES.md file. Release date: $current_date"
      echo -e "${green_color}Done.${reset_color}"
   else
      echo -e "${red_color}Publishing aborted.${reset_color}"
   fi
   echo "${green_color}Done.${green_color}"
   echo -e "${green_color}================================================================================${color_reset}"
}

case "$1" in
    --latest)
       git fetch
       echo -e "${green_color}$LATEST_VERSION${reset_color}"
       exit 0
       ;;
    --major)
       git fetch
       set_major_version
       echo -e "${green_color}Creating MAJOR release: "$FINAL_VERSION"${reset_color}"
       # git tag $FINAL_VERSION
       change_files
       commit_and_push
       exit 0
       ;;
    --rc)
       git fetch
       set_rc_version
       echo -e "${green_color}Creating RELEASE CANDIDATE (RC): "$FINAL_VERSION"${reset_color}"
       # git tag $FINAL_VERSION
       change_files
       commit_and_push
       exit 0
      ;;
    --top)
       git tag | sort --version-sort | tail "-$2"
       exit 0
       ;;

esac

