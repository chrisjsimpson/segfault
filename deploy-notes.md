
ansible-playbook -vv -i inventory.yml playbooks/main.yml

to ansible:


Somtimes a vps is provisioned without a dns resolver
on ubuntu 20.04 to set the dns resolver: 
https://www.ricmedia.com/set-permanent-dns-nameservers-ubuntu-debian-resolv-conf/

#Install pip:
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
pip install --user virtualenv
echo "PATH=$PATH:/root/.local/bin" >> ~/.bash_profile

# uwsgi 

pip3.8 install uWSGI==2.0.19.1

# TLS / letsencrypt
uses acme.sh

acme.sh --issue -d segfault.app -d '*.segfault.app' --dns  --yes-I-know-dns-manual-mode-enough-go-ahead-please

acme.sh  --install-cert -d segfault.app -d '*.segfault.app' --cert-file /etc/ssl/segfault.app/segfault.app.cer --key-file /etc/ssl/segfault.app/segfault.app.key --fullchain-file /etc/ssl/segfault.app/fullchain.cer --reloadcmd "service apache2 force-reload"
