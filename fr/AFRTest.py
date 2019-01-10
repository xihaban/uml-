#-*- encoding=utf-8 -*-

from fr.arcsoft import CLibrary, ASVL_COLOR_FORMAT, ASVLOFFSCREEN, c_ubyte_p, FaceInfo, AFD_FSDKLibrary
from fr.arcsoft.utils import BufferInfo, ImageLoader
from fr.arcsoft.AFD_FSDKLibrary import *
from fr.arcsoft.AFR_FSDKLibrary import *
from ctypes import *
import traceback

APPID = c_char_p(b'Ef7bAzxGtRrTtcwdbwwaubcNnr28yhRT3ajtgyx2pD2k')
FD_SDKKEY = c_char_p(b'32KN5MHiJPQ4kB1ReJLuy2JJ199GocUT1kXcAMVyUBPm')
FR_SDKKEY = c_char_p(b'32KN5MHiJPQ4kB1ReJLuy2JfVLvmHddzShgtowQb6R4w')
FD_WORKBUF_SIZE = 20 * 1024 * 1024
FR_WORKBUF_SIZE = 40 * 1024 * 1024
MAX_FACE_NUM = 50
bUseYUVFile = False
bUseBGRToEngine = True

def doFaceDetection(hFDEngine, inputImg):
    faceInfo = []

    pFaceRes = POINTER(AFD_FSDK_FACERES)()
    ret = AFD_FSDK_StillImageFaceDetection(hFDEngine, byref(inputImg), byref(pFaceRes))
    if ret != 0:
        return faceInfo

    faceRes = pFaceRes.contents
    if faceRes.nFace > 0:
        for i in range(0, faceRes.nFace):
            rect = faceRes.rcFace[i]
            orient = faceRes.lfaceOrient[i]
            faceInfo.append(FaceInfo(rect.left,rect.top,rect.right,rect.bottom,orient))

    return faceInfo

def extractFRFeature(hFREngine, inputImg,faceInfo):

        faceinput = AFR_FSDK_FACEINPUT()
        faceinput.lOrient = faceInfo.orient
        faceinput.rcFace.left = faceInfo.left
        faceinput.rcFace.top = faceInfo.top
        faceinput.rcFace.right = faceInfo.right
        faceinput.rcFace.bottom = faceInfo.bottom

        faceFeature = AFR_FSDK_FACEMODEL()
        ret = AFR_FSDK_ExtractFRFeature(hFREngine, inputImg, faceinput, faceFeature)
        if ret != 0:
            return None

        try:
            return faceFeature.deepCopy()
        except Exception as e:
            traceback.print_exc()
            print(e.message)
            return None


def compareFaceSimilarity(hFDEngine, hFREngine, inputImgA, inputImgB):
        # Do Face Detect
        faceInfosA = doFaceDetection(hFDEngine, inputImgA)
        if len(faceInfosA) < 1:
            return 0.0
        faceInfosB = doFaceDetection(hFDEngine, inputImgB)
        if len(faceInfosB) < 1:
            return 0.0

        #Extract Face Feature
        faceFeatureA = extractFRFeature(hFREngine, inputImgA, faceInfosA[0])
        if faceFeatureA == None:
            return 0.0
        faceFeatureB = extractFRFeature(hFREngine, inputImgB, faceInfosB[0])
        if faceFeatureB == None:
            faceFeatureA.freeUnmanaged()
            return 0.0
        #calc similarity between faceA and faceB
        fSimilScore = c_float(0.0)
        ret = AFR_FSDK_FacePairMatching(hFREngine, faceFeatureA, faceFeatureB, byref(fSimilScore))
        faceFeatureA.freeUnmanaged()
        faceFeatureB.freeUnmanaged()
        if ret != 0:
            return 0.0
        return fSimilScore

def loadYUVImage(yuv_filePath, yuv_width, yuv_height, yuv_format):
    yuv_rawdata_size = 0

    inputImg = ASVLOFFSCREEN()
    inputImg.u32PixelArrayFormat = yuv_format
    inputImg.i32Width = yuv_width
    inputImg.i32Height = yuv_height
    if ASVL_COLOR_FORMAT.ASVL_PAF_I420 == inputImg.u32PixelArrayFormat:
        inputImg.pi32Pitch[0] = inputImg.i32Width
        inputImg.pi32Pitch[1] = inputImg.i32Width // 2
        inputImg.pi32Pitch[2] = inputImg.i32Width // 2
        yuv_rawdata_size = inputImg.i32Width * inputImg.i32Height * 3 // 2
    elif ASVL_COLOR_FORMAT.ASVL_PAF_NV12 == inputImg.u32PixelArrayFormat:
        inputImg.pi32Pitch[0] = inputImg.i32Width
        inputImg.pi32Pitch[1] = inputImg.i32Width
        yuv_rawdata_size = inputImg.i32Width * inputImg.i32Height * 3 // 2
    elif ASVL_COLOR_FORMAT.ASVL_PAF_NV21 == inputImg.u32PixelArrayFormat:
        inputImg.pi32Pitch[0] = inputImg.i32Width
        inputImg.pi32Pitch[1] = inputImg.i32Width
        yuv_rawdata_size = inputImg.i32Width * inputImg.i32Height * 3 // 2
    elif ASVL_COLOR_FORMAT.ASVL_PAF_YUYV == inputImg.u32PixelArrayFormat:
        inputImg.pi32Pitch[0] = inputImg.i32Width * 2
        yuv_rawdata_size = inputImg.i32Width * inputImg.i32Height * 2
    elif ASVL_COLOR_FORMAT.ASVL_PAF_RGB24_B8G8R8 == inputImg.u32PixelArrayFormat:
        inputImg.pi32Pitch[0] = inputImg.i32Width * 3
        yuv_rawdata_size = inputImg.i32Width * inputImg.i32Height * 3
    else:
        exit(0)

    # load YUV Image Data from File
    f = None
    try:
        f = open(yuv_filePath, u'rb')
        imagedata = f.read(yuv_rawdata_size)
    except Exception as e:
        traceback.print_exc()
        print(e.message)
        exit(0)
    finally:
        if f is not None:
            f.close()

    if ASVL_COLOR_FORMAT.ASVL_PAF_I420 == inputImg.u32PixelArrayFormat:
        inputImg.ppu8Plane[0] = cast(imagedata, c_ubyte_p)
        inputImg.ppu8Plane[1] = cast(addressof(inputImg.ppu8Plane[0].contents) + (inputImg.pi32Pitch[0] * inputImg.i32Height), c_ubyte_p)
        inputImg.ppu8Plane[2] = cast(addressof(inputImg.ppu8Plane[1].contents) + (inputImg.pi32Pitch[1] * inputImg.i32Height // 2), c_ubyte_p)
        inputImg.ppu8Plane[3] = cast(0, c_ubyte_p)
    elif ASVL_COLOR_FORMAT.ASVL_PAF_NV12 == inputImg.u32PixelArrayFormat:
        inputImg.ppu8Plane[0] = cast(imagedata, c_ubyte_p)
        inputImg.ppu8Plane[1] = cast(addressof(inputImg.ppu8Plane[0].contents) + (inputImg.pi32Pitch[0] * inputImg.i32Height), c_ubyte_p)
        inputImg.ppu8Plane[2] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[3] = cast(0, c_ubyte_p)
    elif ASVL_COLOR_FORMAT.ASVL_PAF_NV21 == inputImg.u32PixelArrayFormat:
        inputImg.ppu8Plane[0] = cast(imagedata, c_ubyte_p)
        inputImg.ppu8Plane[1] = cast(addressof(inputImg.ppu8Plane[0].contents) + (inputImg.pi32Pitch[0] * inputImg.i32Height), c_ubyte_p)
        inputImg.ppu8Plane[2] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[3] = cast(0, c_ubyte_p)
    elif ASVL_COLOR_FORMAT.ASVL_PAF_YUYV == inputImg.u32PixelArrayFormat:
        inputImg.ppu8Plane[0] = cast(imagedata, c_ubyte_p)
        inputImg.ppu8Plane[1] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[2] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[3] = cast(0, c_ubyte_p)
    elif ASVL_COLOR_FORMAT.ASVL_PAF_RGB24_B8G8R8 == inputImg.u32PixelArrayFormat:
        inputImg.ppu8Plane[0] = cast(imagedata, c_ubyte_p)
        inputImg.ppu8Plane[1] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[2] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[3] = cast(0, c_ubyte_p)
    else:
        exit(0)

    inputImg.gc_ppu8Plane0 = imagedata
    return inputImg

def loadImage(filePath):

    inputImg = ASVLOFFSCREEN()
    if bUseBGRToEngine:
        bufferInfo = ImageLoader.getBGRFromFile(filePath)
        inputImg.u32PixelArrayFormat = ASVL_COLOR_FORMAT.ASVL_PAF_RGB24_B8G8R8
        inputImg.i32Width = bufferInfo.width
        inputImg.i32Height = bufferInfo.height
        inputImg.pi32Pitch[0] = bufferInfo.width*3
        inputImg.ppu8Plane[0] = cast(bufferInfo.buffer, c_ubyte_p)
        inputImg.ppu8Plane[1] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[2] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[3] = cast(0, c_ubyte_p)
    else:
        bufferInfo = ImageLoader.getI420FromFile(filePath)
        inputImg.u32PixelArrayFormat = ASVL_COLOR_FORMAT.ASVL_PAF_I420
        inputImg.i32Width = bufferInfo.width
        inputImg.i32Height = bufferInfo.height
        inputImg.pi32Pitch[0] = inputImg.i32Width
        inputImg.pi32Pitch[1] = inputImg.i32Width // 2
        inputImg.pi32Pitch[2] = inputImg.i32Width // 2
        inputImg.ppu8Plane[0] = cast(bufferInfo.buffer, c_ubyte_p)
        inputImg.ppu8Plane[1] = cast(addressof(inputImg.ppu8Plane[0].contents) + (inputImg.pi32Pitch[0] * inputImg.i32Height), c_ubyte_p)
        inputImg.ppu8Plane[2] = cast(addressof(inputImg.ppu8Plane[1].contents) + (inputImg.pi32Pitch[1] * inputImg.i32Height // 2), c_ubyte_p)
        inputImg.ppu8Plane[3] = cast(0, c_ubyte_p)
    inputImg.gc_ppu8Plane0 = bufferInfo.buffer

    return inputImg


if __name__ == u'__main__':

    # init Engine
    pFDWorkMem = CLibrary.malloc(c_size_t(FD_WORKBUF_SIZE))
    pFRWorkMem = CLibrary.malloc(c_size_t(FR_WORKBUF_SIZE))

    hFDEngine = c_void_p()
    ret = AFD_FSDK_InitialFaceEngine(APPID, FD_SDKKEY, pFDWorkMem, c_int32(FD_WORKBUF_SIZE), byref(hFDEngine), AFD_FSDK_OPF_0_HIGHER_EXT, 32, MAX_FACE_NUM)
    if ret != 0:
        CLibrary.free(pFDWorkMem)
        exit(0)

    # print FDEngine version
    versionFD = AFD_FSDK_GetVersion(hFDEngine)

    hFREngine = c_void_p()
    ret = AFR_FSDK_InitialEngine(APPID, FR_SDKKEY, pFRWorkMem, c_int32(FR_WORKBUF_SIZE), byref(hFREngine))
    if ret != 0:
        AFD_FSDKLibrary.AFD_FSDK_UninitialFaceEngine(hFDEngine)
        CLibrary.free(pFDWorkMem)
        CLibrary.free(pFRWorkMem)
        exit(0)


    versionFR = AFR_FSDK_GetVersion(hFREngine)

    if bUseYUVFile:
        filePathA = u'001_640x480_I420.YUV'
        yuv_widthA = 640
        yuv_heightA = 480
        yuv_formatA = ASVL_COLOR_FORMAT.ASVL_PAF_I420

        filePathB = u'003_640x480_I420.YUV'
        yuv_widthB = 640
        yuv_heightB = 480
        yuv_formatB = ASVL_COLOR_FORMAT.ASVL_PAF_I420

        inputImgA = loadYUVImage(filePathA, yuv_widthA, yuv_heightA, yuv_formatA)
        inputImgB = loadYUVImage(filePathB, yuv_widthB, yuv_heightB, yuv_formatB)
    else:
        filePathA = u'../static/facedata/base/52.jpg'
        filePathB = u'../static/facedata/confirm/20180726&194716.jpg'

        inputImgA = loadImage(filePathA)
        inputImgB = loadImage(filePathB)


    # release Engine
    AFD_FSDK_UninitialFaceEngine(hFDEngine)
    AFR_FSDK_UninitialEngine(hFREngine)

    CLibrary.free(pFDWorkMem)
    CLibrary.free(pFRWorkMem)


def checkFace(path0,path1):

    # init Engine
    pFDWorkMem = CLibrary.malloc(c_size_t(FD_WORKBUF_SIZE))
    pFRWorkMem = CLibrary.malloc(c_size_t(FR_WORKBUF_SIZE))

    hFDEngine = c_void_p()
    ret = AFD_FSDK_InitialFaceEngine(APPID, FD_SDKKEY, pFDWorkMem, c_int32(FD_WORKBUF_SIZE), byref(hFDEngine),
                                     AFD_FSDK_OPF_0_HIGHER_EXT, 32, MAX_FACE_NUM)
    if ret != 0:
        CLibrary.free(pFDWorkMem)
        exit(0)


    versionFD = AFD_FSDK_GetVersion(hFDEngine)


    hFREngine = c_void_p()
    ret = AFR_FSDK_InitialEngine(APPID, FR_SDKKEY, pFRWorkMem, c_int32(FR_WORKBUF_SIZE), byref(hFREngine))
    if ret != 0:
        AFD_FSDKLibrary.AFD_FSDK_UninitialFaceEngine(hFDEngine)
        CLibrary.free(pFDWorkMem)
        CLibrary.free(pFRWorkMem)
        exit(0)

    # print FREngine version
    versionFR = AFR_FSDK_GetVersion(hFREngine)

    # load Image Data
    if bUseYUVFile:
        filePathA = u'001_640x480_I420.YUV'
        yuv_widthA = 640
        yuv_heightA = 480
        yuv_formatA = ASVL_COLOR_FORMAT.ASVL_PAF_I420

        filePathB = u'003_640x480_I420.YUV'
        yuv_widthB = 640
        yuv_heightB = 480
        yuv_formatB = ASVL_COLOR_FORMAT.ASVL_PAF_I420

        inputImgA = loadYUVImage(filePathA, yuv_widthA, yuv_heightA, yuv_formatA)
        inputImgB = loadYUVImage(filePathB, yuv_widthB, yuv_heightB, yuv_formatB)
    else:
        filePathA = path0
        filePathB = path1

        inputImgA = loadImage(filePathA)
        inputImgB = loadImage(filePathB)

    res=str(compareFaceSimilarity(hFDEngine, hFREngine, inputImgA, inputImgB))[8:11]
    return float(res)

    # release Engine
    AFD_FSDK_UninitialFaceEngine(hFDEngine)
    AFR_FSDK_UninitialEngine(hFREngine)

    CLibrary.free(pFDWorkMem)
    CLibrary.free(pFRWorkMem)
