# collectd-consul
consul monitoring script for collectd + grafana dashboard

## Installation
1. Copy consul.py into your CollectD python plugins directory
2. Configure the plugin in CollectD
3. Restart CollectD

## Configuration

```
<LoadPlugin python>
    Globals true
</LoadPlugin>

<Plugin python>
    ModulePath "/path/to/python/modules"

    Import consul
    <Module consul>
        Host "localhost"
        Port 8500
        Verbose false
    </Module>
</Plugin>
```

## Metrics

```
collectd/consul_server_0/consul/
├── services_auctioneer
│   └── gauge
│       └── isok.wsp
├── services_auctioneer_checks_auctioneer
│   └── gauge
│       ├── critical.wsp
│       ├── passing.wsp
│       └── warning.wsp
├── services_auctioneer_checks_serfHealth
│   └── gauge
│       ├── critical.wsp
│       ├── passing.wsp
│       └── warning.wsp
```
