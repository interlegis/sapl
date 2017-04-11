import os
from genkey import generate_secret

key = None
if os.path.exists('data/secret.key'):
    with open('data/secret.key', 'r') as f:
        key = f.read()
else:
    with open('data/secret.key', 'w') as f:
        key = generate_secret()
        f.write("%s" % key)

with open(".env", "w") as f:

    f.write("DATABASE_URL = postgresql://postgres:@localhost:/sapldb\n")
    f.write("SECRET_KEY: %s\n" % key)

    # TODO use template and dict?
    f.write("DEBUG=False\n")

    f.write("EMAIL_USE_TLS = True\n")

    f.write("EMAIL_PORT = 587\n")
    EMAIL_PORT = os.environ['EMAIL_PORT'] if 'EMAIL_PORT' in os.environ else ''
    f.write("EMAIL_PORT: %s\n" % EMAIL_PORT)

    EMAIL_HOST = os.environ['EMAIL_HOST'] if 'EMAIL_HOST' in os.environ else ''
    f.write("EMAIL_HOST: %s\n" % EMAIL_HOST)

    EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER'] if 'EMAIL_HOST_USER' in os.environ else ''
    f.write("EMAIL_HOST_USER: %s\n" % EMAIL_HOST_USER)

    EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD'] if 'EMAIL_HOST_PASSWORD' in os.environ else ''
    f.write("EMAIL_HOST_PASSWORD: %s\n" % EMAIL_HOST_PASSWORD)


# SECRET_KEY=TravisTest
# DEBUG=False
# EMAIL_USE_TLS = True
# EMAIL_PORT = 587
# EMAIL_HOST = ''
# EMAIL_HOST_USER = ''
# EMAIL_HOST_PASSWORD = ''
