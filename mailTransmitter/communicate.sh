#! /usr/bin/env bash

inpipe=/tmp/py_in_pipe
outpipe=/tmp/py_out_pipe
qtin=/tmp/qt_in_pipe
qtout=/tmp/qt_out_pipe

rm -rf $inpipe $outpipe $qtin $qtout

if [[ ! -p $inpipe ]]; then
    mkfifo $inpipe
fi

if [[ ! -p $outpipe ]]; then
    mkfifo $outpipe
fi

if [[ ! -p $qtin ]]; then
    mkfifo $qtin
fi
if [[ ! -p $qtout ]]; then
    mkfifo $qtout
fi

echo "start" 
while true
do
    if read line <$outpipe; then
        if  [[ $line == "Successfully Ending" ]]; then
            break
        fi
        echo $line >$qtin
        
        echo "waiting input: $line"
        read input <$qtout 
        #echo $input
        echo $input >$inpipe
    fi
done 
