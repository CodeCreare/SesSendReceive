# coding: UTF-8
import io
import re
import os
import datetime
import logging
logger = logging.getLogger()




def GetOs():
	if os.name == 'nt':
		return 'Windows'
	elif os.name == 'posix':
		return 'Linux'
	else:
		logger.critical('os.name==%s', os.name)



def GetRunPath():
	run_path = os.getcwd()
#	run_path = 'E:/Work/ReSkill/1_SoftwareLanguage/Python/'		# DEBUG
	return run_path



def Sleep(sec, str='', openlog=False):
	import time
	if str != '':
		logger.info(str)
	else:
		logger.debug('sleep %d sec' % sec)

	if openlog:
		CB_OpenLogAtTerminate()
	time.sleep(sec)



def GetSetting(file_or_files, path=''):
	if path == '':
		path = GetRunPath()

	if type(file_or_files) == list:
		files	= file_or_files
		for fname in files:
			file	= os.path.join(path, fname)
			if os.path.exists(file):
				break

	else:
		fname	= file_or_files
		file	= path + fname

	lines	= ReadLinesExCr(file)
	settings	= {}
	for line in lines:
		m_setting = re.match(r'([^\s]+)\s+([^\s].+)' , line)
		if re.match(r'^\/\/' , line):
			continue
		elif m_setting:
			key = m_setting.group(1)
			val = m_setting.group(2)
			settings[key]	= val
	return settings



def GetFileFromHere(file_here, relas):
	dir_here	= os.path.dirname(file_here)
	file		= dir_here
	for rela in relas:
		file	= os.path.join(file, rela)

	return file



def MakeFolderIfNotExist(folder):
	if False == os.path.exists(folder):
		os.mkdir(folder)



s_logs = []
def Log(str):
	s_logs.append(str)



def GetCaller():
	import inspect
	file_caller	= inspect.stack()[2].filename
	tmp, fname	= os.path.split(file_caller)
	fname		= fname.replace('.py', '')
	return fname


s_file_detaillog	= ''
s_file_errorlog		= ''
s_open_when_end		= False
def InitLogging(log_level, open_when_end=False):
	global s_file_detaillog
	global s_file_errorlog
	global s_open_when_end

	caller				= GetCaller()
	s_open_when_end		= open_when_end
	handler_format		= logging.Formatter('%(asctime)s [%(levelname)-7s] %(filename)-12s:%(lineno)4d [%(funcName)s] %(message)s', datefmt='%m/%d %H:%M:%S')

	# Debug - ファイル出力(詳細)
	s_file_detaillog	= os.path.join('..', '..', 'Log', caller + '_DetailLog_' + GetCurrentTimeStr() + '.txt')
	handler_debug 		= logging.FileHandler(s_file_detaillog, 'w', encoding='utf-8')
	handler_debug.setLevel(logging.DEBUG)
	handler_debug.setFormatter(handler_format)
	logger.addHandler(handler_debug)
	# Info - 標準出力
	handler_info 		= logging.StreamHandler()
	handler_info.setLevel(logging.INFO)
	handler_info.setFormatter(handler_format)
	logger.addHandler(handler_info)
	# Error - ファイル出力(エラー)
	s_file_errorlog		= os.path.join('..', '..', 'Log', caller + '_ErrorLog_' + GetCurrentTimeStr() + '.txt')
	handler_warning 	= logging.FileHandler(s_file_errorlog, 'w', encoding='utf-8')
	handler_warning.setLevel(logging.WARNING)
	handler_warning.setFormatter(handler_format)
	logger.addHandler(handler_warning)
	# Critical - 強制終了
	logger.addHandler(HandlerCriticalLog(logging.CRITICAL))
	
	logger.setLevel(log_level)													# ログレベル設定
	import atexit
	atexit.register(CB_OpenLogAtTerminate)												# プログラム終了時処理


class HandlerCriticalLog(logging.StreamHandler):
	def emit(self, record):
		if logging.CRITICAL <= record.levelno:
			global s_open_when_end
			s_open_when_end	= True
			import sys
			sys.exit(1)


def CB_OpenLogAtTerminate():
	global s_open_when_end
	if s_open_when_end:
		OpenLogFile()
		s_open_when_end	= False


def OpenLogFile():
	global s_file_detaillog
	global s_file_errorlog
	if os.path.getsize(s_file_errorlog) == 0:
		OpenFiles([s_file_detaillog])
	else:
		OpenFiles([s_file_detaillog, s_file_errorlog])



def CB_JsonSerial(obj):
	if isinstance(obj, (datetime.datetime, datetime.date)):						# 日付型の場合には、文字列に変換します
		return obj.isoformat()
	logger.critical('Type %s not serializable' % type(obj))

def MakeIndentJsonStr(data):
	import json
	strjson	= json.dumps(data, indent = 2, ensure_ascii=False, default=CB_JsonSerial)
	return strjson



def MakeShortStr(str_org, len_max):
	lines		= str_org.split('\n')
	str_line	= ''
	for line in lines:
		line	= line.strip()
		if line != '':
			str_line	= StrIfNotEmpty(str_line, '⏎　')
			str_line	+= line

	len_half	= int(len_max / 2)
	if len(str_line) < len_max:
		return str_line

	str_short	= str_line[:len_half] + '　～省略～　' + str_line[len(str_line) - len_half:]
	str_short	= str_short.strip()
	return str_short



def SnapshotFile(file):
	if file == '':
		file	= 'Snapshot_Temp.txt'
	return file


def SnapshotIsExpired(min_expire, file=''):
	if min_expire == -1:
		return True

	file	= SnapshotFile(file)
	if not os.path.exists(file):
		return True

	tm		= os.path.getmtime(file)
	dt_file	= datetime.datetime.fromtimestamp(tm)
	dt_ex	= dt_file + datetime.timedelta(minutes = min_expire)
	dt_now	= datetime.datetime.now()
	logger.debug('dt_ex=%s (%s + %d) <> dt_now=%s' % (dt_ex, dt_file, min_expire, dt_now))
	if dt_ex < dt_now:
		return True
	else:
		return False


def SnapshotSave(data, file=''):
	import json
	jsonstr	= json.dumps(data)
	file	= SnapshotFile(file)

	path	= os.path.dirname(file)
	if path != '':
		os.makedirs(path, exist_ok=True)
	fh = io.open(file, 'w')
	fh.write(jsonstr)
	fh.close()
	logger = logging.getLogger()
	logger.info('SnapshotSave file=%s' % file)


def SnapshotLoad(file=''):
	file	= SnapshotFile(file)

	fh = io.open(file, 'r')
	jsonstr	= fh.read()
	fh.close()

	import json
	data	= json.loads(jsonstr)
	logger = logging.getLogger()
	logger.info('SnapshotLoad file=%s' % file)
	return data



def ReadLines(file, enc='utf-8'):
	with open(file, 'r', encoding=enc) as fh:
		lines = fh.readlines()
	fh.close()
	for pos in range(len(lines)):
		lines[pos] = lines[pos].replace('\n', '')
	return lines



# ReadLines へ切替えていく
def ReadLinesExCr(file, enc='utf-8'):
	return ReadLines(file, enc)



def WriteLines2File(file, lines, enc='UTF8'):
	fh_out = io.open(file, 'w', encoding=enc)
	for line in lines:
		fh_out.write(line + '\n')



def MakeTitleStr(keys):
	strtitle	= ''
	for key in keys:
		strtitle	+= str(key) + ','
	return strtitle

def MakeRecordStr(record, keys):
	strrecord	= ''
	for key in keys:
		if key in record:
			str_value	= str(record[key])
			if ',' in str_value:
				str_value	= str_value.replace(',', '，')
			strrecord	+= str_value + ','
		else:
			strrecord	+= '＜Empty＞,'
	return strrecord

def WriteRecords2Csv(file, records, keys, enc='sjis'):
	title	= MakeTitleStr(keys)
	lines	= []
	lines.append(title)
	for l in range(len(records)):
		record		= records[l]
		strrecord	= MakeRecordStr(record, keys)
		lines.append(strrecord)
	WriteLines2Csv(file, lines, enc)


def WriteLines2Csv(file, lines, enc='sjis'):
	logger.debug('file=%s len=%d' % (file, len(lines)))
	import codecs
	codecs.register_error('none', lambda e: ('?', e.end))
	fh_out		= open(file, 'w', encoding=enc, errors='none')
	for line in lines:
		fh_out.write(line + '\n')
	fh_out.close()



def GetCurrentTimeStr():
	import pytz
	tm_now	= datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
	str_jst	= tm_now.strftime('%Y%m%d_%H%M%S')
	return str_jst



def GetTmStr(tm, show_y=True, show_md=True, show_w=False, show_hm=True, show_s=False, show_zero=True, zero_space=False, sep_ymd='/', sep_hms=':', sep_dh=' '):
	if tm == None:
		tm	= datetime.datetime.now()
	if show_zero:
		str_fmt	= '%02d'
	elif zero_space:
		str_fmt	= '%2d'
	else:
		str_fmt	= '%d'

	strtm	= ''
	if show_y:
		strtm	+= str(tm.year)

	if show_md:
		if len(strtm) != 0:
			strtm	+= sep_ymd
		strtm	+= (str_fmt + sep_ymd + str_fmt) % (tm.month, tm.day)

	if show_w:
		weeks	= ['月', '火', '水', '木', '金', '土', '日']
		strtm	+= '(' + weeks[tm.weekday()] + ')'

	strtm	+= sep_dh

	if show_hm:
		strtm	+= (str_fmt + sep_hms + '%02d') % (tm.hour, tm.minute)

	if show_s:
		strtm	+= (sep_hms + '%02d') % (tm.second)

	return strtm.strip(sep_dh)


def GetTmStr_MDW(tm=None, show_zero=False, zero_space=False):
	return GetTmStr(tm, show_y=False, show_w=True, show_hm=False, show_zero=show_zero, zero_space=zero_space)


def GetTmStr_MDW_HM(tm=None, show_zero=False, zero_space=False):
	return GetTmStr(tm, show_y=False, show_w=True, show_zero=show_zero, zero_space=zero_space)


def GetTmStr_HM(tm=None, show_zero=False, zero_space=False):
	return GetTmStr(tm, show_y=False, show_md=False, show_zero=show_zero, zero_space=zero_space)



def ConvJst2Utc(dt_jst):
	import pytz
	tmzn_bef	= pytz.timezone('Asia/Tokyo')
	tmzn_aft	= pytz.timezone('UTC')
	dt_jst		= tmzn_bef.localize(dt_jst)
	dt_utc		= dt_jst.astimezone(tmzn_aft)
	return dt_utc


def ConvUtc2Jst(dt_utc):
	import pytz
	tmzn_bef	= pytz.timezone('UTC')
	tmzn_aft	= pytz.timezone('Asia/Tokyo')
	dt_utc		= tmzn_bef.localize(dt_utc)
	dt_jst		= dt_utc.astimezone(tmzn_aft)
	return dt_jst



def RoundDatetime2Day(dt):
	dtd	= datetime.date(dt.year, dt.month, dt.day)
	return dtd



def Add1Month(dt):
	for d in range(31):
		dt	= dt + datetime.timedelta(days=1)
		if dt.day == 1:
			return dt

	logger.critical('Add1Month Error')



def GetToday():
	dt_now		= datetime.datetime.now()
	dtd_now		= RoundDatetime2Day(dt_now)
	return dtd_now



def SelectTargetDay():
	inp		= input(' --------- <0:Today 1:Yesterday 2:2days ago 3days ago(LastFriday)> ---------\n')
	days	= int(inp)
	if days < 0 or 3 < days:
		logger.critical('0 - 3 までのみ対応してます。')

	dtd_today	= GetToday()
	dtd_target	= dtd_today - datetime.timedelta(days = days)
	return dtd_target



def ConvDt2Ut(dt):
	if type(dt) is datetime.date:
		dt	= datetime.datetime(dt.year, dt.month, dt.day, 0 ,0, 0)
	ut	= dt.timestamp()
	ut	= int(ut)
	return ut



def ConvMin2Timestr(min):
	if min < 0:
		return '-'
	m		= min % 60
	h		= int(min / 60)
	dt		= datetime.datetime(2021, 1, 1, h, m)
	strtime	= str(dt.strftime('%H:%M'))
	return strtime



def ConvTime2Min(timedata):
	dt_time	= timedata
	if type(timedata) is str:
		dt_time	= datetime.datetime.strptime(timedata, '%H:%M')

	dt_dawn		= datetime.datetime(dt_time.year, dt_time.month, dt_time.day, 0, 0)
	delta		= dt_time - dt_dawn
	secs		= delta.total_seconds()
	mins		= secs / 60
	mins		= int(mins)
	return mins



def ConvSec2Time(sec):
	if sec < 0:
		return datetime.time()
	s		= sec % 60
	m		= int(sec / 60)
	m		= m % 60
	h		= int(sec / 60 / 60)
	tm		= datetime.time(hour=h, minute=m, second=s)
	return tm



def GetUpdatedDate(file):
	import pathlib
	if not os.path.exists(file):
		mtime	= 0
	else:
		p		= pathlib.Path(file)
		stat	= p.stat()
		mtime	= stat.st_mtime
	dt		= datetime.datetime.fromtimestamp(mtime)
	return dt



def OpenFiles(files):
	str_os	= GetOs()
	if str_os == 'Linux':
		return

	for file in files:
		if file != '' and (not os.path.exists(file) and not re.match('http', file)):
			logger.error(file + 'は存在しません！')
			continue

		if re.match('.+xlsx*', file):
			OpenWithExcel(file)
		elif re.match('http', file):
			OpenWithChrome(file)
		elif file != '' and file != '-':
			OpenWithExplorer(file)


def OpenWithExplorer(file):
	if not ':' in file:
		dir	= os.getcwd()
		file	= os.path.join(dir, file)

	import subprocess
	subprocess.run('explorer {}'.format(file))


def OpenWithChrome(file):
	exes = [
		r'C:\Program Files\Google\Chrome\Application\chrome.exe',
		r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
	]
	for exe in exes:
		if os.path.exists(exe):
			str_exe	= exe + ' "' + file + '"'
			import subprocess
			subprocess.Popen(str_exe)


def OpenWithExcel(file):
	exes = [
		r'C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE',
		r'C:\Program Files (x86)\Microsoft Office\Office14\EXCEL.EXE',
	]
	file	= file.replace('/', '\\')
	for exe in exes:
		if os.path.exists(exe):
			str_exe	= exe + ' "' + file + '"'
			import subprocess
			subprocess.Popen(str_exe)



def TrimLines(lines):
	lines_new = []
	for line in lines:
		if not re.match('^#', line):
			line = re.sub('\n', '', line)
			if not re.match('^\s*\Z', line):
				lines_new.append(line)
	return lines_new



def GetZenkakuLength(str_zen):
	import unicodedata
	len	= 0
	for c in str(str_zen):
		if unicodedata.east_asian_width(c) in ('F', 'W', 'A'):
			len += 2
		else:
			len += 1
	return len



def PadSpace2ZenkakuStr(str_org, len_tgt, isspace_zen=False, conv_orgstr=False):
	len			= len_tgt
	str_ret		= str_org
	if conv_orgstr:
		str_ret	= ConvHankaku2Zenkau(str_ret)

	len_space	= len - GetZenkakuLength(str_ret)
	if isspace_zen:
		str_ret	= str(str_ret) + '　' * int(len_space / 2)
	else:
		str_ret	= str(str_ret) + ' ' * len_space

	lenzen	= GetZenkakuLength(str_ret)
	if len < lenzen:
		str_ret	= str_ret[0:len-1]
		if isspace_zen:
			str_ret	= str_ret + '　'
			amari = len % 2
			if amari != 0:
				logger.error('amari != 0, str_org=%s, len_tgt=%d' % (str_org, len_tgt))

		else:
			str_ret	= str_ret + ' '

	return str_ret



def RegPtnKanjiStr(kana=True):
	if kana:
		ptn	= '\u2E80-\u2FDF\u3005-\u3007\u3041-\u309F\u30A1-\u30FF\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\U00020000-\U0002EBEF'
	else:
		ptn	= '\u2E80-\u2FDF\u3005-\u3007\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\U00020000-\U0002EBEF'
	return ptn



def ConvZenkau2Hankaku(str_val):
	str_val	= str_val.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))
	return str_val



def ConvHankaku2Zenkau(str_val):
	str_val	= str(str_val)
	str_val	= str_val.translate(str.maketrans({chr(0x0021 + i): chr(0xFF01 + i) for i in range(94)}))
	str_val = str_val.replace(' ', '　')
	return str_val



def ConvStr2Ordhex(str_in):
	str_out	= ''
	for pos in range(len(str_in)):
		c	= str_in[pos]
		o	= ord(c)
		str_out	= str_out + hex(o) + ','
	return str_out



def StrIfNotEmpty(str, stradd):
	if str == '':
		return str
	else:
		return str + stradd;



def SubStrBetween(str, start, end, empty_if_notfound=True):
	retstr	= str
	if start != '':
		pos	= retstr.find(start)
		if pos == -1:
			if empty_if_notfound:
				return ''
			else:
				return retstr
		retstr	= retstr[pos + len(start):]

	if end != '':
		pos	= retstr.find(end)
		if pos == -1:
			if empty_if_notfound:
				return ''
			else:
				return retstr
		retstr	= retstr[0: pos]

	return retstr



def DetectCharsetFromFile(file):
	import chardet
	with open(file, 'rb') as f:
		b = f.read()
	enc = chardet.detect(b) 
	return enc



def PutStrs2Indent(line, zenkaku, ar_indent_str):
	for indent_str in ar_indent_str:
		len_line	= GetZenkakuLength(line)
		diff		= indent_str[0] - len_line
		if diff < 0:
			if zenkaku:
				pos		= int(indent_str[0] / 2) - 1
				line	= line[0:pos] + '　'
			else:
				pos		= indent_str[0] - 1
				deleting	= True
				while deleting:
					line		= line[0:len(line)-1]
					len_line	= GetZenkakuLength(line)
					if len_line < indent_str[0]:
						deleting = False
						diff	= indent_str[0] - len_line
						line	+= ' ' * diff

		else:
			if zenkaku:
				line	+= '　' * int(diff / 2)
			else:
				line	+= ' ' * diff

		str_tgt	= str(indent_str[1])
		if str_tgt == '0':
			str_tgt = ' '
		if zenkaku:
			str_tgt	= ConvHankaku2Zenkau(str_tgt)

		line	+= str_tgt

	return line



def Debug_RegPtnKanjiStr():
	kanji	= RegPtnKanjiStr()
	ptnsrc	= '[^' + kanji + ']*[' + kanji + ']+\s[' + kanji + ']+[^' + kanji + ']*'
	ptnsrc	= '[^' + kanji + ']*[' + kanji + ']+\s[' + kanji + ']+'
	ptn = re.compile(ptnsrc)
	m = ptn.match('佐藤 敏樹10')
	print('m=', m)


def Debug_GetTmStr():
	tm	= datetime.datetime.now()
	print(GetTmStr(tm, show_w=True, show_s=True))
	print(GetTmStr(tm, show_s=True, sep_ymd='', sep_hms='', sep_dh='_'))
	print(GetTmStr(tm, show_y=False, show_md=False, sep_hms='', sep_dh='_'))
	print(GetTmStr(tm, show_s=True))
	print(GetTmStr_MDW(tm))
	print(GetTmStr_MDW_HM(tm))
	print(GetTmStr_HM(tm))


def Debug_DetectCharsetFromFile():
	file	= r'C:\work\Sky\2_情報共有\2_関西カーエレ\関西カーエレMTG_20211213_Dummy.txt'
	file	= r'C:\work\Sky\2_情報共有\2_関西カーエレ\関西カーエレMTG_20211213.txt'
	enc = DetectCharsetFromFile(file)
	logger.info('enc=%s' % enc)


def Debug_OpenFiles():
	files	= [r'https://www.atsumitakeshi.com/python/py_os_discrim.html']
	OpenFiles(files)


def Debug_ConvUtc2Jst():
	import dateutil.tz
	dt_utc	= datetime.datetime(2022, 1, 8, 19, 55, tzinfo=dateutil.tz.gettz('UTC'))
	dt_jst	= ConvUtc2Jst(dt_utc)
	logger.info('dt_utc=%s -> dt_jst=%s', dt_utc, dt_jst)
	dt_utc	= ConvJst2Utc(dt_jst)
	logger.info('dt_jst=%s -> dt_utc=%s', dt_jst, dt_utc)


def Debug():
#	Debug_RegPtnKanjiStr()
#	Debug_GetTmStr()
#	Debug_DetectCharsetFromFile()
#	Debug_OpenFiles()
	Debug_ConvUtc2Jst()



if __name__ == '__main__':
	InitLogging(logging.DEBUG, False)
	Debug()



