# -*- coding: utf-8 -*-

import sys
import os
import shutil
import re


extensions = {'mp4':'Video', 'avi':'Video','ts':'Video', 'srt':'Subtitles', 'pdf':'Documents\\PDFs', 'ppt':'Documents\\PPTs', 'docx':'Documents\\DOCs', 'csv':'Documents\\CSVs', 'xls':'Documents\\XLSs', 'pptx':'Documents\\PPTs', 'doc':'Documents\\DOCs', 'exe':'Programs', 'djvu':'Books', 'epub':'Books', 'py':'Code', 'ipynb':'Code','c':'Code', 'cpp':'Code', 'm':'Code',\
			 'jpg':'Images', 'jpeg':'Images', 'png':'Images', 'json':'JSON', 'rar':'Compressed', 'zip':'Compressed', 'tz':'Compressed', 'gz':'Compressed', 'torrent':'Torrents'}

path = 'C:\\Users\\Rohit\\Downloads'
others = 'Others'

count = 0
exists = re.compile(r'Destination path \'.+\' already exists')
duplicates = re.compile(r'( \(\d+\)\..+)$')


for item in os.listdir(path):
	if os.path.isfile(os.path.join(path, item)):
		parts = item.split('.')
		ext = parts[-1]
		count += 1
		destination = extensions.get(ext)

		res = duplicates.search(item)
		if res != None:
			main_name = duplicates.sub('.' + ext, item)

			if main_name in os.listdir(path):
				print('Duplicate Found:', item)
				continue

		if destination == None:
			destination = extensions.get(ext.upper())
			if destination == None:
				destination = others

		if not os.path.exists(os.path.join(path, destination)):
			os.mkdir(os.path.join(path, destination))		

		try:
			shutil.move(os.path.join(path, item), os.path.join(path, destination))

		except shutil.Error as e:
			exc = str(e)
			res = exists.search(exc)
			if res != None:
				print(exc)

