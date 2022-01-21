from flask import Flask
from flask import request
import json
from datetime import datetime
from configparser import SafeConfigParser

from drive_helpers import main_quickstart

from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive.file']

# The ID of a sample document.
DOCUMENT_ID = '195j9eDD3ccgjQRttHhJPymLJUCOUjs-jmwTrekvdjFE'
SERVICE_ACCOUNT_FILE = 'service-account.json'


"""
Read in and parse config options
"""

config = SafeConfigParser()
config.read('config')

listen_port = config.get('main', 'listen_port')
include_channel = config.get('main', 'include_channel')
date_format = config.get('main', 'tag_date_format')
compact_date= config.get('main', 'compact_date')


app = Flask(__name__)

@app.route("/test")
def slash_2():
	return "hello"

@app.route("/save", methods=['POST'])
def save_to_docs():
	form_text = request.form["text"]
	channel_name = request.form["channel_name"]

	creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

	try:
		service = build('docs', 'v1', credentials=creds)
		# drive_service = build('drive', 'v3', credentials=creds)

		# Retrieve the documents contents from the Docs service.
		# document = service.documents().get(documentId=DOCUMENT_ID).execute()
		print("Service starting")

		# print('The title of the document is: {}'.format(document.get('title')))

		# title = 'My Document'
		# body = {
		#     'title': title
		# }
		# doc = service.documents() \
		#     .create(body=body).execute()
		# print('Created document with title: {0}'.format(
		#     doc.get('title')))
		# documentId = doc.get('documentId')
		text_from_user = form_text
		text_to_insert = "Channel [{}]:\n {}\n\n".format(channel_name, text_from_user)
		requests = [
			{
				'insertText': {
					'location': {
						'index': 1,
					},
					'text': text_to_insert
				}
			},
		]
		documentId = '1WYbL7QHcEo-_Asq_YBFAldiVNS2SBOiH9MCvLfec97A'


		result = service.documents().batchUpdate(
			documentId=documentId, body={'requests': requests}).execute()
		print("Wrote to doc {}".format(documentId))

		"""
		The following code is used to add permissions to a file
		"""
		# def callback(request_id, response, exception):
		#     if exception:
		#         # Handle error
		#         print (exception)
		#     else:
		#         print ("Permission Id: {}".format(response.get('id')))

		# batch = drive_service.new_batch_http_request(callback=callback)
		# user_permission = {
		#     'type': 'user',
		#     'role': 'writer',
		#     'emailAddress': 'kevin.cottington@affirm.com'
		# }
		# batch.add(drive_service.permissions().create(
		#         fileId='1WYbL7QHcEo-_Asq_YBFAldiVNS2SBOiH9MCvLfec97A',
		#         body=user_permission,
		#         fields='id',
		# ))
		# batch.execute()
	except HttpError as err:
		print(err)
	return "Saved to https://docs.google.com/document/d/1WYbL7QHcEo-_Asq_YBFAldiVNS2SBOiH9MCvLfec97A/edit"


@app.route("/TF", methods=['POST'])
def get_tf_pr():
	form_text = request.form["text"]
	if len(form_text) > 0:
		output = "[TF PR{}](https://github.com/Affirm/terraffirm/pull/{})".format(form_text, form_text)
		data = {
			"response_type": "in_channel",
			"text": output
		}
	else:
		data = {
			"response_type": "ephemeral",
			"text": "Error: No status message entered. Please try again.",
			}
	response = app.response_class(
				response=json.dumps(data),
				status=200,
				mimetype='application/json'
		)
	return response

@app.route("/shriya-test")
def shriya_test():
  return main_quickstart()

@app.route("/standup", methods=['GET', 'POST'])
def slash_command():
		"""
		Retrieve text field from the form request which contains
		the message entered by the user who invoked the slash command
		"""
		form_text = request.form["text"]
		channel = "_"+request.form["channel_name"] if include_channel == 'True' else " "
		short_tag_date = "%m%d%Y" if date_format == 'mdy' else "%Y%m%d"
		long_tag_date =	"%m_%d_%Y" if date_format == 'mdy' else "%Y_%m_%d"
		tag_date = short_tag_date if compact_date == 'True' else long_tag_date


		if len(form_text) > 0:
				"""
				Format the return message with markdown with standup hash tags
				"""
				output = "##### Status Update for {}\n\n{}\n\n#standup-{} #standup".format(
					datetime.strftime(datetime.now(), "%A %-d %B %Y"),
					form_text,
					datetime.strftime(datetime.now(), tag_date+channel),
				)

				"""
				Create data json object to return to Mattermost with
				response_type = in_channel (everyone sees) or ephemeral (only sender sees)
				text = the message to send
				"""
				data = {
						"response_type": "in_channel",
						"text": output,
				}
		else:
				"""
				If the user didn't type a message send a note that only
				they see about typing a message
				"""
				data = {
						"response_type": "ephemeral",
						"text": "Error: No status message entered. Please try again.",
				}

		"""
		Create the response object to send to Mattermost with the
		data object written as json, 200 status, and proper mimetype
		"""
		response = app.response_class(
				response=json.dumps(data),
				status=200,
				mimetype='application/json'
		)
		return response


if __name__ == '__main__':
		app.run(host='0.0.0.0', port=listen_port, debug=False)
