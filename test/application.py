import os, json, requests
from cached_property import cached_property
from datetime import datetime
import urllib.parse

class Application(object):
  def __init__(self, root):
    self.root = root

  def file(self, *path):
    return os.path.join(self.root, *path)

  def github(self, *path):
    return 'https://www.github.com/{}/tree/master/{}'.format(os.getenv('GH_REPO'), self.file(*path))

  def github_raw(self, *path):
    return 'https://raw.githubusercontent.com/{}/master/{}'.format(os.getenv('GH_REPO'), self.file(*path))

  @cached_property
  def basic(self):
    with open(self.file('application.json')) as f:
      return json.load(f)

  @cached_property
  def essay_url(self):
    return self.github('essay.md')

  @cached_property
  def essay_length(self):
    return len(requests.get(self.github_raw('essay.md')).text.split(' '))

  @cached_property
  def submitted(self):
    return self.submitted_raw.strftime('%B %d, %Y')

  @cached_property
  def submitted_raw(self):
    return datetime.utcfromtimestamp(os.path.getmtime(self.root))

  @cached_property
  def challenge_is_dynamic(self):
    return bool(os.path.exists(self.file('challenge', 'build.sh')))

  @cached_property
  def challenge_url(self):
    if self.challenge_is_dynamic:
      return self.github('challenge', 'build.sh')
    else:
      return 'https://htmlpreview.github.io/?{}'.format(self.github_raw('challenge', 'index.html'))

  @cached_property
  def challenge_label(self):
    if self.challenge_is_dynamic:
      return 'Build Script'
    else:
      return 'Preview'

  @cached_property
  def resume_domain(self):
    return urllib.parse.urlparse(self.basic['resume']).hostname

  @cached_property
  def website_domain(self):
    if not 'website' in self.basic:
      return None
    return urllib.parse.urlparse(self.basic['website']).hostname

  @cached_property
  def linkedin_username(self):
    return self.basic['linkedin'].split('/')[-1]

class Applications(object):
  def __init__(self, root='applications'):
    self.root = root
    self.dirs = filter(lambda d: not d.startswith('.'), os.listdir(root))

  def __iter__(self):
    return self

  def __next__(self):
    return Application(os.path.join(self.root, next(self.dirs)))
