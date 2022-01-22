# UTF8
import datetime
import sys
sys.path.append('../../Function/Common')
import Common
sys.path.append('../../Function/OtherSvc')
import SesIf
import logging
logger = logging.getLogger()




def Execute():
	# 受信
	dtd_start	= datetime.date(2022, 1, 18)
	mails		= SesIf.GetMailsDays(dtd_start, 4)
	for mail in mails:
		logger.info('subject=%s', mail['subject'])
		logger.info('from=%s', mail['from'])
		logger.info('bodys=%s', mail['bodys'])

	# 送信
	str_from	= 'SESに登録してるドメイン、当システムならtekitou@codecreare.com'
	str_dest	= '受信確認できるメールアドレス、Gmailアドレス等'
	str_subject	= 'Title'
	str_text	= 'This is Text'
	str_html	= '<html><head></head><body>Test 21:26</body></html>'
	str_html	= '<html><head></head><body><a href="https://www.google.com/">Google</a></body></html>'
	SesIf.SendMail(str_from, str_dest, str_subject, str_text, str_html)



if __name__ == '__main__':
	Common.InitLogging(logging.DEBUG, True)
	Execute()



