import smtplib
import email.message
import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

class sendGmail():

	def __init__(self,userName, password):
		self.gmail_user = userName  
		self.gmail_password = password
		self.recipients = []
		self.subject = ""
		self.body = ""
		self.attachments = []
		self.subject

	def addRecipients(self, recipients):
		self.recipients += recipients

	def addAttachments(self, attachments):
		self.attachments.append(attachments)

	def send(self):
		assert isinstance(self.recipients, list)
		if len(self.recipients) != 0:
			msg = MIMEMultipart()
			msg['From'] = self.gmail_user
			msg['To'] = COMMASPACE.join(self.recipients)
			msg['Date'] = formatdate(localtime=True)
			msg['Subject'] = self.subject

			msg.attach(MIMEText(self.body))

			for f in self.attachments or []:
				with open(f, "rb") as fil:
					part = MIMEApplication(
					fil.read(),
					Name=basename(f)
					)
					part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
					msg.attach(part)

			smtp = smtplib.SMTP_SSL('smtp.gmail.com', 465)
			smtp.ehlo()
			smtp.login(self.gmail_user, self.gmail_password)
			smtp.sendmail(self.gmail_user, self.recipients, msg.as_string())
			smtp.close()


	def send_mail(self,send_to, subject, text, files=None):
		assert isinstance(send_to, list)
		msg = MIMEMultipart()
		msg['From'] = self.gmail_user
		msg['To'] = COMMASPACE.join(send_to)
		msg['Date'] = formatdate(localtime=True)
		msg['Subject'] = subject

		msg.attach(MIMEText(text))

		for f in files or []:
			with open(f, "rb") as fil:
				part = MIMEApplication(
				fil.read(),
				Name=basename(f)
				)
				part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
				msg.attach(part)


		smtp = smtplib.SMTP_SSL('smtp.gmail.com', 465)
		smtp.ehlo()
		smtp.login(self.gmail_user, self.gmail_password)
		#print send_to
		smtp.sendmail(self.gmail_user, send_to, msg.as_string())
		smtp.close()

