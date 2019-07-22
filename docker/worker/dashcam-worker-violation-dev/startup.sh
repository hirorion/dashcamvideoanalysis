#!/bin/bash

id $CUR_USER_NAME
if [ $? = 1 ]; then
    echo "$CUR_USER_NAME was not found"
    exit 1
fi

HOME=/home/$CUR_USER_NAME SHELL=/bin/bash su - $CUR_USER_NAME #-c "source venv/bin/activate; cp /mnt/worker/ai/define.py feature-irric/; cd feature-irric; ./rabbit_receive_ai.py"
