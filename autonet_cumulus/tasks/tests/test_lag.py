import pytest

from autonet.core.objects import lag as an_lag

from autonet_cumulus.tasks import lag as lag_task


def test_get_evpn_es_map(test_show_evpn_es_data):
    expected = {
        'bond10': '03:be:e9:af:17:3f:60:00:00:14',
        'bond20': '03:be:e9:af:17:3f:60:00:00:0a'
    }
    assert lag_task.get_evpn_es_map(test_show_evpn_es_data) == expected


@pytest.mark.parametrize('test_bond_name, expected', [
    ('bond20', [
        an_lag.LAG(name='bond20', members=['swp3'],
                   evpn_esi='03:be:e9:af:17:3f:60:00:00:0a')
    ]),
    (None, [
        an_lag.LAG(name='bond10', members=['swp10', 'swp11'],
                   evpn_esi='03:be:e9:af:17:3f:60:00:00:14'),
        an_lag.LAG(name='bond20', members=['swp3'],
                   evpn_esi='03:be:e9:af:17:3f:60:00:00:0a')
    ])
])
def test_get_lags(test_show_bonds_data, test_show_evpn_es_data,
                  test_bond_name, expected):
    bonds = lag_task.get_lags(test_show_bonds_data, test_show_evpn_es_data,
                              test_bond_name)
    assert bonds == expected


@pytest.mark.parametrize('test_lag, expected', [
    (an_lag.LAG(name='bond5', evpn_esi='03:be:e9:1a:17:21:60:00:00:f0',
                members=['swp5', 'swp6', 'swp8']),
     [
         'add bond bond5 evpn mh es-id 240',
         'add bond bond5 evpn mh es-sys-mac be:e9:1a:17:21:60'
     ]),
    (an_lag.LAG(name='app-svr-9', evpn_esi='03:fa:2f:da:dd:82:e5:00:0f:0a',
                members=['swp20', 'swp21']),
     [
         'add bond app-svr-9 evpn mh es-id 3850',
         'add bond app-svr-9 evpn mh es-sys-mac fa:2f:da:dd:82:e5'
     ])
])
def test_generate_lag_esi_commands(test_lag, expected):
    commands = lag_task.generate_lag_esi_commands(test_lag)
    assert commands == expected


@pytest.mark.parametrize('test_lag, expected', [
    (an_lag.LAG(name='bond5', evpn_esi='03:be:e9:1a:17:21:60:00:00:f0',
                members=['swp5', 'swp6', 'swp8']),
     [
         'add bond bond5 bond mode 802.3ad',
         'del interface swp5',
         'del interface swp6',
         'del interface swp8',
         'add interface swp5',
         'add interface swp6',
         'add interface swp8',
         'add bond bond5 bond slaves swp5',
         'add bond bond5 bond slaves swp6',
         'add bond bond5 bond slaves swp8',
         'add bond bond5 evpn mh es-id 240',
         'add bond bond5 evpn mh es-sys-mac be:e9:1a:17:21:60'
     ]),
    (an_lag.LAG(name='app-svr-9', evpn_esi=None,
                members=['swp20', 'swp21']),
     [
         'add bond app-svr-9 bond mode 802.3ad',
         'del interface swp20',
         'del interface swp21',
         'add interface swp20',
         'add interface swp21',
         'add bond app-svr-9 bond slaves swp20',
         'add bond app-svr-9 bond slaves swp21'
     ])
])
def test_generate_create_lag_commands(test_lag, expected):
    commands = lag_task.generate_create_lag_commands(test_lag)
    assert commands == expected


@pytest.mark.parametrize('test_lag, test_original_lag, update, expected', [
    (an_lag.LAG(name='bond5', evpn_esi='03:be:e9:1a:17:21:60:00:00:f0',
                members=['swp5', 'swp6', 'swp8']),
     an_lag.LAG(name='bond5', evpn_esi='03:be:e9:1a:17:21:60:00:00:f0',
                members=['swp5', 'swp6', 'swp11']),
     True,
     [
         'add bond bond5 bond mode 802.3ad',
         'del interface swp8',
         'add interface swp5',
         'add interface swp6',
         'add interface swp8',
         'add bond bond5 bond slaves swp5',
         'add bond bond5 bond slaves swp6',
         'add bond bond5 bond slaves swp8',
         'add bond bond5 evpn mh es-id 240',
         'add bond bond5 evpn mh es-sys-mac be:e9:1a:17:21:60'
     ]),
    (an_lag.LAG(name='bond5', evpn_esi=None,
                members=['swp12', 'swp8']),
     an_lag.LAG(name='bond5', evpn_esi='03:be:e9:1a:17:21:60:00:00:f0',
                members=['swp5', 'swp6', 'swp11']),
     True,
     [
         'add bond bond5 bond mode 802.3ad',
         'del interface swp12',
         'del interface swp8',
         'add interface swp12',
         'add interface swp8',
         'add bond bond5 bond slaves swp12',
         'add bond bond5 bond slaves swp8'
     ]),
    (an_lag.LAG(name='app-svr-9', evpn_esi=None,
                members=['swp20', 'swp21']),
     an_lag.LAG(name='app-svr-9', evpn_esi=None,
                members=['swp20', 'swp21', 'swp22']),
     False,
     [
         'add bond app-svr-9 bond mode 802.3ad',
         'add interface swp20',
         'add interface swp21',
         'add bond app-svr-9 bond slaves swp20',
         'add bond app-svr-9 bond slaves swp21',
         'del bond app-svr-9 bond slaves swp22',
         'del interface swp22',
         'del bond app-svr-9 evpn mh es-id',
         'del bond app-svr-9 evpn mh es-sys-mac'
     ]),
    (an_lag.LAG(name='lag55', evpn_esi=None,
                members=['swp20', 'swp21', 'swp22']),
     an_lag.LAG(name='lag55', evpn_esi='03:be:e9:1a:17:21:60:00:00:f0',
                members=['swp20', 'swp21', 'swp22']),
     False,
     [
         'add bond lag55 bond mode 802.3ad',
         'add interface swp20',
         'add interface swp21',
         'add interface swp22',
         'add bond lag55 bond slaves swp20',
         'add bond lag55 bond slaves swp21',
         'add bond lag55 bond slaves swp22',
         'del bond lag55 evpn mh es-id',
         'del bond lag55 evpn mh es-sys-mac'
     ])
])
def test_generate_update_lag_commands(test_lag, test_original_lag,
                                      update, expected):
    commands = lag_task.generate_update_lag_commands(
        test_lag, test_original_lag, update)
    assert commands == expected


@pytest.mark.parametrize('test_lag_name, expected', [
    ('bond5', ['del bond bond5']),
    ('app-srv-9', ['del bond app-srv-9'])
])
def test_generate_delete_lag_commands(test_lag_name, expected):
    commands = lag_task.generate_delete_lag_commands(test_lag_name)
    assert commands == expected
