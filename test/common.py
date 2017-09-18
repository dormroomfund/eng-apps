import functools, os, base64, subprocess
from contextlib import contextmanager

def with_vars(arg):
  default = None if callable(arg) else arg

  def with_vars_wrapper(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
      if not os.getenv('PRIVATE_KEY'):
        return default
      return f(*args, **kwargs)
    return wrapper

  return with_vars_wrapper(arg) if callable(arg) else with_vars_wrapper

@with_vars
def write_private_key():
  with open('private.pem', 'wb') as f:
    f.write(base64.b64decode(os.environ['PRIVATE_KEY']))

def remove_private_key():
  os.remove('private.pem')

@contextmanager
def private_key():
    write_private_key()
    yield
    remove_private_key()

@with_vars
def hide_private_key():
  del os.environ['PRIVATE_KEY']
  assert not subprocess.run('echo $PRIVATE_KEY', stdout=subprocess.PIPE, shell=True).stdout.strip()

def decrypt_file(infile, outfile):
  subprocess.run([
    'openssl',
    'smime',
    '-decrypt',
    '-binary',
    '-inkey',
    'private.pem',
    '-inform',
    'DEM',
    '-in',
    infile,
    '-out',
    outfile,
  ]).check_returncode()

def _decrypt_files(application_root):
  decrypted = []
  for root, dirs, files in os.walk(application_root):
    for file in files:
      if file.endswith('.enc'):
        infile = os.path.join(root, file)
        outfile = infile[:-4]
        decrypt_file(infile, outfile)
        decrypted.append(outfile)
  return decrypted

@with_vars([])
def decrypt_files(application_root):
  with private_key():
    return _decrypt_files(application_root)

def remove_files(files):
  for file in files:
    os.remove(file)
