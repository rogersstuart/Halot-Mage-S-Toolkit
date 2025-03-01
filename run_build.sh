#!/usr/bin/expect -f

set timeout 10
# Enable logging of the interaction to the console
log_user 1

# Get the scripts directory path from the first argument
set scripts_dir [lindex $argv 0]
puts "Changing directory to $scripts_dir"
cd $scripts_dir

spawn ./build.sh

expect {
    -re ".*:\n" {
        puts "Prompt detected, sending 'y'"
        send "y\r"
        exp_continue
    }
    eof {
        puts "End of file detected"
        exit
    }
    timeout {
        puts "Timeout occurred"
        exit 1
    }
}