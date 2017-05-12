#/bin/bash

KEY=`python gen-key.py`
echo $KEY

sed -e "s/SECRET_KEY = None/SECRET_KEY = $KEY/g" config/env-sample
