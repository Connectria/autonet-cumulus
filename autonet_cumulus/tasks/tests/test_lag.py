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
