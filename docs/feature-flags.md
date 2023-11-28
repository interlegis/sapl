
### Types

Waffle supports three types of feature flippers:

### Flags

_"Flags can be used to enable a feature for specific users, groups, users meeting 
certain criteria (such as being authenticated, or superusers) or a certain percentage 
of visitors."_

https://waffle.readthedocs.io/en/stable/types/flag.html

### Switches

_"Switches are simple booleans: they are on or off, for everyone, all the time.
They do not require a request object and can be used in other contexts, such
as management commands and tasks."_

Enabling/Disabling via CLI (example):

    ./manage.py waffle_switch SOLR_SWITCH on --create

    ./manage.py waffle_switch SOLR_SWITCH off --create


https://waffle.readthedocs.io/en/stable/types/switch.html

### Samples

_"Samples are on a given percentage of the time. They do not require a request 
object and can be used in other contexts, such as management commands and tasks."_

Liga e desliga baseado em amostragem aleatória.

https://waffle.readthedocs.io/en/stable/types/sample.html

### Reference
* Documentation: https://waffle.readthedocs.io/
* Managing from CLI: https://waffle.readthedocs.io/en/stable/usage/cli.html
* Templates: https://waffle.readthedocs.io/en/stable/usage/templates.html
* Views: https://waffle.readthedocs.io/en/stable/usage/views.html
* Decorators: https://waffle.readthedocs.io/en/stable/usage/decorators.html


