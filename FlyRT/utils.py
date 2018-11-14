import os

def file_ops():
	pwd = os.getcwd()
	list_of_files = os.listdir(pwd)

	if "generated_data" in list_of_files:
		os.chdir(pwd+"\\generated_data")
		if "logs" in os.listdir(os.getcwd()):
			pass
		else:
			os.mkdir('logs')
			os.chdir(pwd)
	else:
		os.mkdir('generated_data')
		file_ops()

	if "generated_data" in list_of_files:
		os.chdir(pwd+"\\generated_data")
		if "movies" in os.listdir(os.getcwd()):
			pass
		else:
			os.mkdir('movies')
		os.chdir(pwd)

	return None
