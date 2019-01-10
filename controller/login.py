from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
import os,base64
import datetime
from fr import AFRTest


def page(request):
    return render(request, "login.html")

def getface(request):
    if request.POST:
        time = datetime.datetime.now().strftime('%Y%m%d&%H%M%S')
        strs=request.POST['message']
        imgdata = base64.b64decode(strs)
        try:
            file = open(u'static/facedata/confirm/'+time+'.jpg', 'wb')
            file.write(imgdata)
            file.close()
        except:
            print('as')
        res=AFRTest.checkFace(u'static/facedata/base/52.jpg',u'static/facedata/confirm/'+time+'.jpg')
        if res>=0.6:
            return HttpResponse('panel')
        else:
            return HttpResponse('no')
    else:
        return HttpResponse('no')
