from crud import build_crud

from .models import Country

country_crud = build_crud(
    Country, 'help_path', [
        ['Basic Data',
         [('name', 9), ('continent', 3)],
         [('population', 6), ('is_cold', 6)]
         ],
        ['More Details', [('description', 12)]],
    ])
