import random


def generate_secret():
    return (''.join([random.SystemRandom().choice(
        'abcdefghijklmnopqrst'
        'uvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)]))


if __name__ == '__main__':
    print(generate_secret())
