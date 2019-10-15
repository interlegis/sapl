import django.dispatch

tramitacao_signal = django.dispatch.Signal(providing_args=['post', 'request'])

post_delete_signal = django.dispatch.Signal(providing_args=['instance', 'request'])

post_save_signal = django.dispatch.Signal(providing_args=['instance', 'operation', 'request'])