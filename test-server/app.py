import os
from flask import Flask, request, jsonify
from github import Github

app = Flask(__name__)
github = Github(os.getenv('GH_TOKEN'))

def valid():
  return request.args['valid'] == 'true'

def full_pr_message(valid, message):
  if valid:
    return 'Your application is valid! :sunglasses:'
  else:
    return 'Your application is invalid! **{}**'.format(message)

def create_issue_comment(repo, user):
  if valid():
    return
  title = "Invalid Application: {}".format(user)
  message = 'Hey @{}, your application is invalid! **{}**'.format(user, request.args['message'])
  try:
    issue = repo.get_issues(assignee=user)[0]
  except IndexError:
    repo.create_issue(title, message, user, labels=['application-invalid'])
  else:
    issue.edit(title, message)

def create_pr_comment(pr):
  comment = next(filter(lambda x: x.user.login == os.getenv('GH_USER'), pr.get_issue_comments()), None)
  message = full_pr_message(valid(), request.args.get('message'))
  if comment:
    comment.edit(message)
  else:
    pr.create_issue_comment(message)

@app.route('/')
def hello_world():
  repo = github.get_repo(os.getenv('GH_REPO'))
  user = request.args['user']
  try:
    pr = repo.get_pulls(head='{}:{}'.format(user, request.args['branch']))[0]
  except IndexError:
    create_issue_comment(repo, user)
  else:
    create_pr_comment(pr)

  return jsonify({'error': None})
