#! /usr/bin/env bash

inpipe=/tmp/mail_in_pipe
outpipe=/tmp/mail_out_pipe
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
    #read line<$outpipe
        if  [[ $line == "Successfully Ending" ]]; then
            break
        fi
        #echo "read line"
        echo $line >$qtin
        #while true  
        #do
            if [[ $line == "Successfullu Ending" ]]; then
                break
            fi
        #    read line<$outpipe
        #    echo $line >$qtin
        #done
        #if [[ $line =~ ^Input ]]; then
            #if [[ $line =~ password:$ ]]; then 
            #    read -s -p input <$qtout
            #else
            echo "waiting input: $line"
                read input <$qtout 
            #fi
            #echo "line 48 operated"
            echo $input
            echo $input >$inpipe
        #fi
    fi
done 
