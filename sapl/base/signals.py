import django.dispatch

tramitacao_signal = django.dispatch.Signal(providing_args=['post', 'request'])
