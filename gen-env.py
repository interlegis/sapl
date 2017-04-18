import os
import subprocess
from genkey import generate_secret

key = None
if os.path.exists('data/secret.key'):
    with open('data/secret.key', 'r') as f:
        key = f.read()
else:
    with open('data/secret.key', 'w') as f:
        key = generate_secret()
        f.write("%s" % key)

with open("sapl/.env", "w") as f:

    DATABASE_URL = 'postgresql://sapl:sapl@sapldb:5432/sapl'
    URL = os.environ['DATABASE_URL'] if 'DATABASE_URL' in os.environ else DATABASE_URL

    f.write("DATABASE_URL = %s\n" % URL)
    f.write("SECRET_KEY = %s\n" % key)

    # TODO use template and dict?
    f.write("DEBUG = False\n")

    f.write("EMAIL_USE_TLS = True\n")

    EMAIL_PORT = os.environ['EMAIL_PORT'] if 'EMAIL_PORT' in os.environ else '587'
    f.write("EMAIL_PORT = %s\n" % EMAIL_PORT)

    EMAIL_HOST = os.environ['EMAIL_HOST'] if 'EMAIL_HOST' in os.environ else ''
    f.write("EMAIL_HOST = %s\n" % EMAIL_HOST)

    EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER'] if 'EMAIL_HOST_USER' in os.environ else ''
    f.write("EMAIL_HOST_USER = %s\n" % EMAIL_HOST_USER)

    EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD'] if 'EMAIL_HOST_PASSWORD' in os.environ else ''
    f.write("EMAIL_HOST_PASSWORD = %s\n" % EMAIL_HOST_PASSWORD)


#subprocess.call("./start.sh")
