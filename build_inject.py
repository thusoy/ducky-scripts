import argparse
import os
import subprocess
import sys
import tempfile
from Crypto.PublicKey import RSA
from jinja2 import Template

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--github-user', help='The GitHub user whose keys will'
    ' be preloaded for the pi user. If absent authentication will have to use the '
    ' default password "raspberry".')
    parser.add_argument('-u', '--ssh-user', help='The user to use for sshing to the'
    ' target. Github user will be specified if this is not given.')
    parser.add_argument('-t', '--ssh-target', help='', required=True)
    parser.add_argument('-p', '--ssh-target-pubkey', help='The SSH targets pubkey'
        ' can be specified for complete two-way trust. If absent, any key presented'
        ' will be accepted and enables a MiTM attack. This argument can be given'
        ' several times. Make sure you quote the pubkeys correctly: -p "ssh-rsa <snip>"', nargs='*', default=[])
    parser.add_argument('-k', '--ssh-key', help='The SSH key to use for connecting'
        ' to the target. If not specified, a key will be created and the public part'
        ' echoed when creating the inject binary')
    parser.add_argument('-s', '--script-out', help="Don't encode the script, just"
        ' echo it to stdout', action='store_true')
    parser.add_argument('-o', '--output', default='inject.bin', help='Where to output'
        ' the final binary. Default: %(default)s')
    parser.add_argument('-e', '--encoder', default='encoder.jar', help='Path to the'
        ' encoder. Default: %(default)s')
    
    args = parser.parse_args()
    
    if not (args.ssh_user or args.github_user):
        parser.print_help()
        print('Error: Either --ssh-user or --github-user is required', file=sys.stderr)
        sys.exit(1)

    # Build the script to be passed to the encoder
    build_target = tempfile.NamedTemporaryFile(delete=False)
    for line in build(github_user=args.github_user,
        ssh_target=args.ssh_target, ssh_target_pubkeys=args.ssh_target_pubkey,
        ssh_key=args.ssh_key, ssh_user=args.ssh_user):
        build_target.write((line + '\n').encode('utf-8'))
    build_target.close()

    if args.script_out:
        with open(build_target.name) as fh:
            for line in fh:
                print(line.strip())
    else:
        # Do the actual encoding
        subprocess.check_call(['java',
            '-jar', args.encoder,
            '-l', 'gb.properties',
            '-i', build_target.name,
            '-o', args.output])

    os.remove(build_target.name)


def build(github_user=None, ssh_target=None, ssh_target_pubkeys=None,
          ssh_key=None, ssh_user=None):
    
    ssh_key_file = None
    if ssh_key is None:
        ssh_key_file = tempfile.NamedTemporaryFile(delete=False)
        ssh_private_key = RSA.generate(2048)
        ssh_key_file.write(ssh_private_key.exportKey())
        ssh_key_file.close()
        print('Add this key to authorized_keys on the target host: ')
        subprocess.check_call(['ssh-keygen', '-y', '-f', ssh_key_file.name])
        print()
        ssh_key = ssh_key_file.name
    
    yield 'REM Use to bootstrap raspberry pis headless.'
    yield 'REM Waits for first boot, expands filesystem through raspi-config,'
    yield 'REM then reboots. On next boot will forward ssh through other server and'
    yield 'REM add a known key it will connect with.'
    yield 'DELAY 30000'
    yield 'DELAY 10000'
    yield 'REM Do filesystem expansion'
    yield 'ENTER'
    yield 'DELAY 15000'
    yield 'REM Accept that it will be booted into on next reboot'
    yield 'ENTER'
    yield 'DELAY 2000'
    yield 'REM Click right two times to exit raspi-config'
    yield 'RIGHTARROW'
    yield 'DELAY 300'
    yield 'RIGHTARROW'
    yield 'DELAY 300'
    yield 'REM Click on finish'
    yield 'ENTER'
    yield 'DELAY 2000'
    yield 'REM Drop back to shell'
    yield 'RIGHTARROW'
    yield 'DELAY 300'
    yield 'ENTER'
    yield 'DELAY 4000'
    yield 'STRING sudo -i'
    yield 'ENTER'
    yield 'DELAY 1000'

    tunnel_context = {
        'ssh_user': ssh_user or github_user,
        'ssh_target': ssh_target,
        'no_strict_checking': len(ssh_target_pubkeys) == 0,
    }
    yield from place_file('/etc/init.d/ssh-tunnel', 'ssh-tunnel.sh', tunnel_context)

    yield 'DELAY 500'
    yield 'STRING chmod +x /etc/init.d/ssh-tunnel'
    yield 'ENTER'
    yield 'DELAY 300'

    if ssh_target_pubkeys:
        yield from place_ssh_known_hosts(ssh_target, ssh_target_pubkeys)

    yield 'DELAY 500'
    yield 'REM Exit sudo'
    yield 'STRING exit'
    yield 'ENTER'
    yield 'DELAY 300'
    yield 'ENTER'
    yield 'STRING mkdir .ssh'
    yield 'ENTER'
    yield 'DELAY 200'
    yield 'STRING chmod 700 .ssh'
    yield 'ENTER'
    yield 'DELAY 200'

    yield from place_file('.ssh/id_rsa', ssh_key)

    yield 'DELAY 200'
    yield 'STRING chmod 600 .ssh/id_rsa'
    yield 'ENTER'
    yield 'DELAY 200'

    yield from place_file('/tmp/bootstrap.sh', 'bootstrap.sh', {'github_user': github_user})

    yield 'STRING sudo bash /tmp/bootstrap.sh'
    yield 'ENTER'

    if ssh_key_file:
        os.remove(ssh_key_file.name)


def place_ssh_known_hosts(host, known_host_keys):
    yield 'STRING cat > /etc/ssh/ssh_known_hosts <<"EOF"'
    yield 'ENTER'
    for known_host_key in known_host_keys:
        yield 'STRING {} {}'.format(host, known_host_key)
        yield 'ENTER'
    yield 'STRING EOF'
    yield 'ENTER'


def place_file(path, source_file, context={}):
    yield 'STRING cat > {} <<"EOF"'.format(path)
    yield 'ENTER'
    with open(source_file) as fh:
        template = Template(fh.read())
    for block in template.stream(**context):
        for line in block.split('\n'):
            if line:
                yield 'STRING {}'.format(line)
            yield 'ENTER'
    yield 'STRING EOF'
    yield 'ENTER'

if __name__ == '__main__':
    main()
