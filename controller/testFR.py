from fr import AFRTest
from django.http import HttpResponse

def face(request):
    res = AFRTest.checkFace(u'static/facedata/base/52.jpg', u'static/facedata/base/52.jpg')
    return HttpResponse(res)