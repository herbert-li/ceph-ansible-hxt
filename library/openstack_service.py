#!/usr/bin/python

import subprocess

from ansible.module_utils.basic import *  # NOQA

fields = {
    'user': {'required': True, 'type': "str"},
    'service': {'required': False, 'type': "str"},
    'password': {'required': True, 'type': "str"},
    'type': {'required': True, 'type': "str"},
    'description': {'required': True, 'type': "str"},
    'url': {'required': True, 'type': "str"},
    'public_url': {'required': True, 'type': "str"},
    'keystone_url': {'required': True, 'type': "str"},
    'admin_password': {'required': True, 'type': "str"},
}

oscli = '/usr/bin/openstack'


def _os_env(admin_pass, keystone_url):
    return {
        'OS_PROJECT_DOMAIN_NAME': 'Default',
        'OS_USER_DOMAIN_NAME': 'Default',
        'OS_PROJECT_NAME': 'service',
        'OS_USERNAME': 'admin',
        'OS_PASSWORD': admin_pass,
        'OS_AUTH_URL': keystone_url,
        'OS_IDENTITY_API_VERSION': '3',
    }


def _create_user(user, password, nova_env, dryrun):
    before = None
    try:
        args = [oscli, 'user', 'show', user]
        with open('/dev/null', 'w') as f:
            subprocess.check_output(args, env=nova_env, stderr=f)

        args = [oscli, 'role', 'list', '--project=service',
                '--format=json', '--user', user]
        roles = subprocess.check_output(args, env=nova_env)
        roles = json.loads(roles)
    except:
        roles = []
        before = 'Service User() role()\n'
        args = [oscli, 'user', 'create', '--domain=default',
                '--password', password, user]
        if not dryrun:
            subprocess.check_output(args, env=nova_env)

    is_admin = False
    for role in roles:
        if role['Name'] == 'admin':
            is_admin = True
            break
    if is_admin:
        before = 'Service User(%s) role(admin)\n' % user
    else:
        if not before:
            before = 'Service User(%s) role()\n' % user
        args = [oscli, 'role', 'add', '--project=service',
                '--user', user, 'admin']
        if not dryrun:
            subprocess.check_output(args, env=nova_env)
    return before, 'Service User(%s) role(admin)\n' % user


def _create_service(service, description, type, nova_env, dryrun):
    before = None
    try:
        args = [oscli, 'service', 'show', service]
        with open('/dev/null', 'w') as f:
            subprocess.check_output(args, env=nova_env, stderr=f)
            before = 'Service: %s\n' % service
    except:
        before = 'Service:\n'
        args = [oscli, 'service', 'create', '--name', service,
                '--description', description, type]
        if not dryrun:
            subprocess.check_output(args, env=nova_env)
    return before, 'Service: %s\n' % service


def _get_endpoints(nova_env):
    args = [oscli, 'endpoint', 'list', '--format=json']
    out = subprocess.check_output(args, env=nova_env)
    return json.loads(out)


def _create_endpoint(endpoints, type, interface, url, nova_env, dryrun):
    before = ''
    for ep in endpoints:
        if ep['Service Type'] == type and ep['Interface'] == interface:
            if ep['URL'] != url:
                before = 'Endpoint(%s, %s) = %s\n' % (
                    type, interface, ep['URL'])
                args = [oscli, 'endpoint', 'delete', ep['ID']]
                if not dryrun:
                    subprocess.check_output(args, env=nova_env)
            else:
                before = 'Endpoint(%s, %s) = %s\n' % (type, interface, url)
    args = [oscli, 'endpoint', 'create', '--region=RegionOne',
            type, interface, url]
    after = 'Endpoint(%s, %s) = %s\n' % (type, interface, url)
    if not dryrun and before != after:
        subprocess.check_call(args, env=nova_env)
    return before, after


def main():
    module = AnsibleModule(argument_spec=fields, supports_check_mode=True)
    diff = {'before': '', 'after': ''}
    changed = False

    nova_env = _os_env(
        module.params['admin_password'], module.params['keystone_url'])

    if module.params['user'] != 'keystone':
        before, after = _create_user(
            module.params['user'], module.params['password'],
            nova_env, module.check_mode)
        if before != after:
            changed = True
        diff['before'] += before
        diff['after'] += after

    service = module.params.get('service')
    if not service:
        service = module.params['user']
    before, after = _create_service(
        service, module.params['description'],
        module.params['type'], nova_env, module.check_mode)
    if before != after:
        changed = True
    diff['before'] += before
    diff['after'] += after

    endpoints = _get_endpoints(nova_env)
    for intf in ('internal', 'admin'):
        before, after = _create_endpoint(
            endpoints, module.params['type'], intf, module.params['url'],
            nova_env, module.check_mode)
        if before != after:
            changed = True
        diff['before'] += before
        diff['after'] += after

    # Added the logic to add public endpoints
    before, after = _create_endpoint(
        endpoints, module.params['type'], 'public', module.params['public_url'],
        nova_env, module.check_mode)
    if before != after:
        changed = True
    diff['before'] += before
    diff['after'] += after

    module.exit_json(changed=changed, diff=diff)


if __name__ == '__main__':
    main()
