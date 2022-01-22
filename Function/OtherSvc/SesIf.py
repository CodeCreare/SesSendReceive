# coding: UTF-8
import boto3
import email
import dateutil
import datetime
import sys
sys.path.append('../../Function/Common')
import Common
sys.path.append('../../Function/Aws')
import SecretPassOtherSvc
import logging
logger = logging.getLogger()




def RetriveBodyStr(obj_msg, charset):
#	str_payload	= obj_msg.get_payload(decode=False)
#	logger.debug('str_payload(decode=False)=%s' % str_payload)
	str_payload	= obj_msg.get_payload(decode=True)
#	logger.debug('str_payload=%s' % str_payload)
	if charset == 'None':
		str_body	= str_payload
	else:
		str_body	= str_payload.decode(charset, 'ignore')
	return str_body


def GetBodyPart(obj_msg):
	str_body		= ''
	charset			= ''
	contenttype		= obj_msg.get_content_type()
	logger.debug('contenttype=%s' % contenttype)
	if 'text' in contenttype:
		charset = str(obj_msg.get_content_charset())
		if charset:
			logger.debug('charset == %s' % charset)
			str_body = RetriveBodyStr(obj_msg, charset)
		else:
			if 'charset=shift_jis' in str(obj_msg.get_payload(decode=True)):
				logger.debug('charset == shift_jis (in payload)')
				str_body = RetriveBodyStr(obj_msg, charset)
			else:
				logger.critical('Cant decode')

	body				= {}
	body['contenttype']	= contenttype
	body['charset']		= charset
	body['str']			= str_body
	return body



def GetBodys(obj_mail):
	bodys = []
	for obj_msg in obj_mail.walk():
		bodys.append(GetBodyPart(obj_msg))
		
	return bodys


def GetBodys_New(obj_mail):
	bodys = []
	logger.info('is_multipart=%d' % (obj_mail.is_multipart()))
	if obj_mail.is_multipart():
		for payload in obj_mail.get_payload():
			bodys.append(GetBodyPart(payload))

	else:
		bodys.append(GetBodyPart(obj_mail))

	return bodys



def GetMailDate(obj_mail):
	dt_msg	= dateutil.parser.parse(obj_mail.get('Date'))
	return dt_msg



def GetMailFrom(obj_mail):
	str_from	= obj_mail.get('From')
	str_disp	= Common.SubStrBetween(str_from, '', '<').strip()
	str_account	= Common.SubStrBetween(str_from, '<', '>')
	return str_account, str_disp



# メールの件名を取得
# https://dev.classmethod.jp/articles/lambda-sort-email/
def GetMailSubject(obj_mail):
	(subject, charaset_subject) = email.header.decode_header(obj_mail['Subject'])[0]

	if charaset_subject == None:
		email_subject = subject
	else:
		email_subject = subject.decode(charaset_subject)

	return email_subject



def GetMailFromS3Obj(obj_s3):
	str_mail		= obj_s3.get()['Body'].read().decode('utf-8')
	obj_mail		= email.message_from_string(str_mail)
	mail			= {}
	mail['subject']	= GetMailSubject(obj_mail)
	mail['from'], mail['from_disp']	= GetMailFrom(obj_mail)
	mail['date']	= GetMailDate(obj_mail)
	mail['bodys']	= GetBodys(obj_mail)
	return mail



def GetS3Bucket():
	akey, skey	= SecretPassOtherSvc.GetAwsKeys()
	str_bucket	= 'codecreare-ses-emails'
	session		= boto3.Session(aws_access_key_id=akey, aws_secret_access_key=skey)
	s3_rsc		= session.resource('s3')
	s3_bucket	= s3_rsc.Bucket(str_bucket)
	return s3_bucket



def GetMailsDays(dtd_start, days_target):
	dtd_end	= dtd_start + datetime.timedelta(days = (days_target - 1))
	mails	= GetMails(dtd_start, dtd_end)
	return mails


def GetMails(dtd_start, dtd_end):
	logger.info('%s ～ %s' % (dtd_start, dtd_end))
	dtd_end		= dtd_end + datetime.timedelta(days = 1)
	s3_bucket	= GetS3Bucket()
	s3_objs		= s3_bucket.objects.filter()
	s3_objs_tgt	= []
	for s3_obj in s3_objs:
		dt_s3_utc	= datetime.datetime(s3_obj.last_modified.year, s3_obj.last_modified.month, s3_obj.last_modified.day, s3_obj.last_modified.hour, s3_obj.last_modified.minute)
		dt_s3_jst	= Common.ConvUtc2Jst(dt_s3_utc)
		dtd_s3_jst	= Common.RoundDatetime2Day(dt_s3_jst)
		logger.debug('dtd_s3_jst=%s(%s), dt_s3_utc=%s', dtd_s3_jst, dt_s3_jst, dt_s3_utc)
		if dtd_start <= dtd_s3_jst and dtd_s3_jst < dtd_end:
			s3_objs_tgt.append(s3_obj)

	mails	= []
	for s3_obj_tgt in s3_objs_tgt:
		mail	= GetMailFromS3Obj(s3_obj_tgt)
		logger.info('Received mail, title=%s' % mail['subject'])
		mails.append(mail)

	for mail in mails:
		logger.debug('subject=%s, from=%s(%s), date=%s' % (mail['subject'], mail['from'], mail['from_disp'], mail['date']))
		for body in mail['bodys']:
			logger.debug('[%s:%s], len=%d, body=%s' % (body['contenttype'], body['charset'], len(body['str']), Common.MakeShortStr(body['str'], 400)))

	return mails



def SetMsgData(str_subject, str_text, str_html=''):
	str_charset	= 'UTF-8'
	data_text	= {}
	data_text['Charset']	= str_charset
	data_text['Data']		= str_text
	data_body	= {}
	data_body['Text']		= data_text
	if str_html != '':
		data_html	= {}
		data_html['Charset']	= str_charset
		data_html['Data']		= str_html
		data_body['Html']		= data_html

	data_subject	= {}
	data_subject['Charset']	= str_charset
	data_subject['Data']	= str_subject

	data_msg	= {}
	data_msg['Subject']		= data_subject
	data_msg['Body']		= data_body
	return data_msg


def SendMail(str_from, str_dest, str_subject, str_text, str_html):
	import botocore.exceptions
	akey, skey	= SecretPassOtherSvc.GetAwsKeys()
	client		= boto3.client('ses', region_name='us-east-1', aws_access_key_id=akey, aws_secret_access_key=skey)
	data_dest	= {	'ToAddresses': [str_dest, ],}
	data_msg	= SetMsgData(str_subject, str_text, str_html)

	try:
		response = client.send_email(Destination= data_dest, Message=data_msg, Source=str_from)
	except botocore.exceptions.ClientError as e:
		logger.critical(e.response['Error']['Message'])
	else:
		logger.info('Email sent! Message ID:' + response['MessageId'])



def Debug_SendMail():
	str_from	= 'systemmail@codecreare.com'
	str_dest	= 'toshikisato0507@gmail.com'
	str_subject	= 'Title'
	str_text	= 'This is Text'
	str_html	= '<html><head></head><body>Test 21:26</body></html>'
	str_html	= '<html><head></head><body><a href="https://www.google.com/">Google</a></body></html>'
	SendMail(str_from, str_dest, str_subject, str_text, str_html)


def Debug_GetMailsDays():
	dtd_start	= Common.GetToday()
	dtd_start	= datetime.date(2022, 1, 8)
	mails		= GetMailsDays(dtd_start, 1)


def Debug():
	Debug_GetMailsDays()
#	Debug_SendMail()



if __name__ == '__main__':
	Common.InitLogging(logging.DEBUG, False)
	Debug()



