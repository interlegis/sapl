from unittest import mock

import rtyaml
from sapl.crispy_layout_mixin import read_layout_from_yaml


def test_read_layout_from_yaml(tmpdir):

    stub_content = '''
ModelName:
  Cool Legend:
  - name:9  place  tiny
  - field  nature:2
  - kind:1  date  unit:5 status
  More data:
  - equalA  equalB  equalC
  - highlander '''

    with mock.patch('sapl.crispy_layout_mixin.read_yaml_from_file') as ryff:
        ryff.return_value = rtyaml.load(stub_content)
        assert read_layout_from_yaml('....', 'ModelName') == [
            ['Cool Legend',
             [('name', 9),  ('place', 2), ('tiny', 1)],
             [('field', 10), ('nature', 2)],
             [('kind', 1), ('date', 3), ('unit', 5), ('status', 3)],
             ],
            ['More data',
             [('equalA', 4), ('equalB', 4), ('equalC', 4)],
             [('highlander', 12)],
             ],
        ]
