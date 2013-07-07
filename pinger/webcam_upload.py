#http://stackoverflow.com/questions/2863406/uploading-file-from-file-object-with-pycurl
# import pycurl

# c = pycurl.Curl()

# values = [
#      ("name", "pic"),
#      ("image", (pycurl.FORM_FILE, "~/Desktop/pic.jpeg"))
# ]

# c.setopt(c.URL, "http://echo.httpkit.com")

# c.setopt(c.HTTPPOST, values)
# c.perform()
# c.close()

#more advanced
#http://stackoverflow.com/questions/12749346/translate-curl-command-to-pycurl
import os
import pycurl

class FileReader:
    def __init__(self, fp):
        self.fp = fp
    def read_callback(self, size):
        return self.fp.read(size)

url = 'http://matter.io/webcamUpload'
#url = 'https://echo.httpkit.com'
filename = '/tmp/webcam.jpg'

c = pycurl.Curl()
c.setopt(c.POST, 1)
c.setopt(c.UPLOAD, 1)
c.setopt(c.USERAGENT, 'Curl')
c.setopt(c.VERBOSE, 1)
c.setopt(c.URL, url)
c.setopt(c.HTTPHEADER, [
    # 'Authorization: Bearer %s' % str(ACCESS_TOKEN),
    'Content-Type: multipart/related',
])
c.setopt(pycurl.READFUNCTION, FileReader(open(filename, 'rb')).read_callback)
filesize = os.path.getsize(filename)
c.setopt(pycurl.INFILESIZE, filesize)

data = [
     # ('metadata', (c.FORM_FILE, 'metadata.txt')),
     # ('type', 'application/json'),
     # ('charset', 'UTF-8'),
     ('file', (c.FORM_FILE, filename)),
     ('type', 'image/jpeg'),
]
c.setopt(c.HTTPPOST, data)
c.perform()
c.close()
