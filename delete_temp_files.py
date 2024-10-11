import os
import sys
import stat
import shutil
import time

path = 'C:\\Users\\Rohit\\AppData\\Local\\Temp'
os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

mode = 0o777
#'0o777' is in octal or we could use this: stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
size = 0

items = os.listdir(path)
if len(items) > 0:
	start = time.time()
	for root, direc, files in os.walk(path):
		for file in files:
			try:
				os.chmod(os.path.join(root, file), mode)
				temp = os.path.getsize(os.path.join(root, file))								
				os.remove(os.path.join(root,file))
				size += temp				
			except WindowsError as e:				
				if e.winerror == 32:
					print('File being used by another process:', file)
					continue
		for folder in direc:
			try:
				os.chmod(os.path.join(root, folder), mode)
				temp = os.path.getsize(os.path.join(root, folder))				
				shutil.rmtree(os.path.join(root, folder))
				size += temp								
			except WindowsError as e:
				if e.winerror == 32:
					print('Folder being used by another process:', folder)
					continue					
	end = time.time()
else:
	print('Nothing to delete!')

# print('\nTime taken: {} seconds'.format(end - start))
print('\nTotal data cleared: {} Bytes'.format(size))
exit()