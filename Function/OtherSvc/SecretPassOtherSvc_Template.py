# UTF8



# AWS(IAM)のアクセスキーとシークレットキー
def GetAwsKeys():
	access_key		= ''
	secret_key		= ''
	return access_key, secret_key



if __name__ == '__main__':
	access_key, secret_key	= GetAwsKeys()
	print(access_key, secret_key)



