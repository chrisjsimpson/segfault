#!/bin/sh

ansible-playbook -vv -i inventory.yml playbooks/main.yml 
