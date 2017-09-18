import os
from flask import Flask, request, jsonify, render_template
from flask_basicauth import BasicAuth
from github import Github
from ..application import Applications

app = Flask(__name__)
app.config['BASIC_AUTH_USERNAME'] = os.getenv('BASIC_AUTH_USERNAME')
app.config['BASIC_AUTH_PASSWORD'] = os.getenv('BASIC_AUTH_PASSWORD')

basic_auth = BasicAuth(app)
github = Github(os.getenv('GH_TOKEN'))

def valid():
  return request.values['valid'].lower() == 'true'

def full_pr_message(valid, message):
  if valid:
    return 'Your application is valid! :sunglasses:'
  else:
    return 'Your application is invalid! **{}**'.format(message)

def create_issue_comment(repo, user):
  title = "Invalid Application: {}".format(user)
  valid_message = 'Thanks @{}, your application has been fixed!'.format(user)
  invalid_message = 'Hey @{}, your application is invalid! **{}**'.format(user, request.values['message'])
  try:
    issue = repo.get_issues(assignee=user)[0]
  except IndexError:
    if not valid():
      repo.create_issue(title, invalid_message, user, labels=['application-invalid'])
  else:
    if valid():
      issue.create_comment(valid_message)
      issue.edit(state='closed')
    else:
      issue.create_comment(invalid_message)

def create_pr_comment(pr):
  comment = next(filter(lambda x: x.user.login == os.getenv('GH_USER'), pr.get_issue_comments()), None)
  message = full_pr_message(valid(), request.values.get('message'))
  if comment:
    comment.edit(message)
  else:
    pr.create_issue_comment(message)

@app.route('/', methods=['POST'])
def api():
  repo = github.get_repo(os.getenv('GH_REPO'))
  user = request.values['user']
  try:
    pr = repo.get_pulls(head='{}:{}'.format(user, request.values['branch']))[0]
  except IndexError:
    create_issue_comment(repo, user)
  else:
    create_pr_comment(pr)

  return jsonify({'error': None})

@app.route('/admin')
@basic_auth.required
def admin():
  applications = sorted(Applications(), key=lambda x: x.submitted_raw)
  return render_template('admin.html', applications=applications)
