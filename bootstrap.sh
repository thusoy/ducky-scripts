update-rc.d ssh-tunnel defaults
{%- if github_user -%}
wget https://github.com/{{ github_user }}.keys -O .ssh/authorized_keys
{%- endif -%}
rm /tmp/bootstrap.sh
reboot
