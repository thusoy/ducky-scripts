from bootstrap_raspberrypi import build

def test_full_build():
    expected = open('testdata/working-handcrafted-script.txt').read()
    ssh_keys = [
        'ssh-ed25519 AAAAC3<snip>Kip',
        'ssh-rsa AAAAB3<snip>YpF',
    ]
    actual = '\n'.join(build(github_user='githubuser', ssh_target='example.com',
        ssh_target_pubkeys=ssh_keys, ssh_key='testdata/test_ssh_key.pem', ssh_user='sshuser'))
    assert actual == expected
