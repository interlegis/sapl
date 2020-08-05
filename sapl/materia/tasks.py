from celery import shared_task

#teste
@shared_task
def adding_task(x, y):
    return x + y