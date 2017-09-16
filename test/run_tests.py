#!/usr/bin/env python3.6

import sys, os, base64, subprocess, multiprocessing, json, traceback, functools

HAS_VARS = os.getenv('TRAVIS_SECURE_ENV_VARS', 'false') == 'true'

class TestFailed(Exception):
  pass

def with_vars(arg):
  default = None if callable(arg) else arg

  def with_vars_wrapper(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
      if not HAS_VARS:
        print('Skipping call to {} (no private key)'.format(f.__name__), file=sys.stderr)
        return default
      return f(*args, **kwargs)
    return wrapper

  return with_vars_wrapper(arg) if callable(arg) else with_vars_wrapper

def fail(s, *args):
  text = s.format(*args)
  print("FATAL: {}".format(text))
  raise TestFailed(text)

def child_fail(s):
  fail('{}\n\n{}', s, traceback.format_exc())

@with_vars
def write_private_key():
  with open('private.pem', 'wb') as f:
    f.write(base64.b64decode(os.environ['PRIVATE_KEY']))

@with_vars
def remove_private_key():
  os.remove('private.pem')

@with_vars
def hide_private_key():
  del os.environ['PRIVATE_KEY']
  assert not subprocess.run('echo $PRIVATE_KEY', stdout=subprocess.PIPE, shell=True).stdout.strip()

@with_vars
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

@with_vars([])
def decrypt_files(application_root):
  write_private_key()
  decrypted = []
  for root, dirs, files in os.walk(application_root):
      for file in files:
        if file.endswith('.enc'):
          infile = os.path.join(root, file)
          outfile = infile[:-4]
          decrypt_file(infile, outfile)
          decrypted.append(outfile)
  remove_private_key()
  return decrypted

def remove_files(files):
  for file in files:
    os.remove(file)

def check_applications():
  for username in os.listdir('applications'):
    check_application(username)

def check_application(username):
  root = os.path.join('applications', username)
  decrypted = decrypt_files(root)
  try:
    start_verify_process(root)
  finally:
    remove_files(decrypted)

def exists(file):
  return os.path.exists(file)

def raise_if_not_exists(file):
  if not exists(file) and (HAS_VARS or not exists('{}.enc'.format(file))):
    fail('{} is required but not found!'.format(file))

def raise_if_empty(file, min_length=100):
  with open(file) as f:
    content = f.read()
  if len(content) < 100:
    fail('{} should be at least {} chars long', file, min_length)

def raise_if_not_executable(file):
  if not os.access(file, os.X_OK):
    fail('{} is not executable', file)

def check_json():
  required_keys = {
    'first_name',
    'last_name',
    'resume',
    'university',
    'grad_year',
    'linkedin',
    'email'
  }
  with open('application.json') as f:
    try:
      application = json.loads(f.read())
    except ValueError:
      fail('invalid JSON in application.json')

  missing = required_keys - set(application.keys())
  if missing:
    fail('missing keys in application.json: {}', missing)

def _verify_application():
  for required in ['application.json', 'essay.txt', 'challenge']:
    raise_if_not_exists(required)

  if exists('application.json'):
    check_json()

  if exists('essay.txt'):
    raise_if_empty('essay.txt')

  index = os.path.join('challenge', 'index.html')
  build = os.path.join('challenge', 'build.sh')

  if exists(build):
    raise_if_not_executable(build)
    result = subprocess.run(build, stdout=subprocess.PIPE, timeout=30)
    if result.returncode != 0:
      fail('{} exited with nonzero status {}', build, result.returncode)
    if not result.stdout:
      fail('{} did not output anything', build)
  elif exists(index):
    raise_if_empty(index)
  else:
    fail('neither {} not {} is present', index, build)

def verify_application(root):
  hide_private_key()
  os.chdir(root)
  try:
    _verify_application()
  except TestFailed:
    raise
  except Exception:
    child_fail('application could not be verified')

def start_verify_process(root):
  pool = multiprocessing.Pool(processes=1, maxtasksperchild=1)
  pool.apply(verify_application, args=(root,))
  pool.close()
  pool.join()

def run():
  try:
    check_applications()
  except TestFailed:
    print('This application is not valid.')
    exit(1)
  else:
    print('This application is valid!')

if __name__ == '__main__':
  multiprocessing.set_start_method('spawn')
  run()
