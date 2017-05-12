import collectd
import json
import urllib2
from urlparse import urljoin


CONSUL_CONFIG = {
    'Host':     'localhost',
    'Port':     8500,
    'Verbose':  False,
}

def configure_callback(conf):
    global CONSUL_CONFIG
    for node in conf.children:
        if node.key == 'Host':
            CONSUL_CONFIG[node.key] = node.values[0]
        elif node.key == 'Port':
            CONSUL_CONFIG[node.key] = int(node.values[0])
        elif node.key == 'Verbose':
            CONSUL_CONFIG[node.key] = bool(node.values[0])
        else:
            collectd.warning('consul plugin: Unknown config key: %s.' % node.key)

def dispatch_value(prefix, key, value, type, type_instance=None):
    if not type_instance:
        type_instance = key

    log_verbose('Sending value: %s/%s=%s' % (prefix, type_instance, value))
    if not value and value != 0:
        return
    try:
        value = int(value)
    except ValueError:
        value = float(value)

    val               = collectd.Values(plugin='consul', plugin_instance=prefix)
    val.type          = type
    val.type_instance = type_instance
    val.values        = [value]
    val.dispatch()

def log_verbose(msg):
    if CONSUL_CONFIG['Verbose'] == False:
        return
    collectd.info('consul plugin: %s' % msg)

def check_consul_status(consul_api_endpoint):
    url = urljoin(consul_api_endpoint, '/v1/agent/self')
    response = urllib2.urlopen(url)
    agent_info = json.load(response)
    agent_address = "{}:{}".format(agent_info['Config']['BindAddr'],agent_info['Config']['Ports']['Server'])
    url = urljoin(consul_api_endpoint, '/v1/status/leader')
    response = urllib2.urlopen(url)
    leader = json.load(response)
    is_leader = 1 if leader == agent_address else 0
    dispatch_value('status', 'leader', is_leader, 'gauge')

    url = urljoin(consul_api_endpoint, '/v1/status/peers')
    response = urllib2.urlopen(url)
    peers = json.load(response)
    dispatch_value('status', 'peers', len(peers), 'gauge')

def check_consul_service(consul_api_endpoint, service):
    url = urljoin(consul_api_endpoint, '/v1/health/service/{}'.format(service))
    response = urllib2.urlopen(url)
    service_info = json.load(response)
    for check in service_info[0]['Checks']:
        check['CheckID'] = check['CheckID'].replace('service:', '')
    return service_info[0]['Checks']

def check_consul_services(consul_api_endpoint):
    url = urljoin(consul_api_endpoint, '/v1/catalog/services')
    response = urllib2.urlopen(url)
    service_list = json.load(response)

    service_check_result = {}
    for service in service_list.keys():
        service_check_result[service] = {}

        service_check_list = check_consul_service(consul_api_endpoint, service)
        for service_check in service_check_list:
            check_name = service_check['CheckID']
            check_status = service_check['Status']

            service_check_result[service][check_name] = {}
            service_check_result[service][check_name]['passing'] = 0
            service_check_result[service][check_name]['warning'] = 0
            service_check_result[service][check_name]['critical'] = 0

            service_check_result[service][check_name][check_status] += 1

        total_ok = 0
        for check in service_check_result[service].keys():
            dispatch_value('services.{}.checks.{}'.format(service, check), 'passing', service_check_result[service][check_name]['passing'], 'gauge')
            dispatch_value('services.{}.checks.{}'.format(service, check), 'warning', service_check_result[service][check_name]['warning'], 'gauge')
            dispatch_value('services.{}.checks.{}'.format(service, check), 'critical', service_check_result[service][check_name]['critical'], 'gauge')
            total_ok += 1
        isok = 1 if total_ok == len(service_check_result[service]) else 0
        dispatch_value('services.{}'.format(service), 'isok', isok, 'gauge')

def read_callback():
    consul_api_endpoint = "http://{}:{}".format(CONSUL_CONFIG['Host'], CONSUL_CONFIG['Port'])

    check_consul_status(consul_api_endpoint)
    check_consul_services(consul_api_endpoint)

# register callbacks
collectd.register_config(configure_callback)
collectd.register_read(read_callback)
