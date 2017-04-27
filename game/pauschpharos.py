#!/usr/bin/python2
# PauschPharos class
# Controls Pausch Bridge light shows
# Author: 	Paul Aluri
# Date:		5/1/2015

import requests

HOST = "http://192.168.1.12"
DEFAULT = "/home/teacher/Pharos_Files/Pausch_V27.006145.wrn"
BLANK = "/home/teacher/Pharos_Files/blank.006145.wrn"
DEFAULT_ID = 1 #default trigger ID

#Example usage:
#
#	from pauschpharos import PauschPharos
#	p = PauschPharos()
#
#	#p.SetBlank() for blank show
#	#p.SetDefault() for default show
#	#p.Upload(filepath) for any show
#	#p.Trigger(id, dict) to send trigger (if no params, set dict to None)

class PauschPharos:
	def __init__(self):
		#Default host, where Pharos controller access is
		self.upload = HOST + '/upload'
		self.trigger = HOST + "/trigger"

	def Upload(self, filename):
		#Needs to be multipart form with header as such:
		#Content-Disposition: name="~project_file"; filename="filename"
		f={'~project_file': open(filename, 'rb')}
		r = requests.post(self.upload, files=f)

	def Trigger(self, tid, params):
		#Really hacky way to set params string
		#Is not URL encoded or anything
		p = ""
		if params:
			p = "?"

			i = 0
			for key in params:
				p += key + "=" + str(params[key])
				if i < len(params) - 1:
					p += "&"
				i += 1
		else:
			p = "?conditions=0"

		request_string = "%s/%d%s" % (self.trigger, tid, p)
		r = requests.get(request_string)

	#Clear to blank show
	def SetBlank(self):
		self.Upload(BLANK)

	#Bring back default show
	def SetDefault(self):
		self.Upload(DEFAULT)
		self.Trigger(DEFAULT_ID, None)

if(__name__ == '__main__'):
  p = PauschPharos()
  p.SetDefault()
