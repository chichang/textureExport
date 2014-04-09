#!/X/tools/binlinux/xpython
from types import ListType, TupleType
import subprocess
import os, re, sys
import simplejson as json
from math import *
import time, datetime
import OpenEXR
import shutil
from . import Odict as dict
from .. import globals
from .. import logger

global ICONVERT
global ICONVERTOPTIONS
global ICONVERTDEFAULTS
global OIIO_PATH
global OIIO_DATATYPES
global ratDefaults
global DEFAULT_LODS

__version__ = '0.58'

OIIO_PATH = globals.OIIO_PATH
ICONVERT  = globals.ICONVERT

ICONVERTOPTIONS = dict(
    compression = [
        "deflate", "none"
        ],
    )

ICONVERTDEFAULTS = dict(
    compression = "deflate",
    )

ratDefaults = dict(
    compression = ICONVERTOPTIONS.get("compression"),
    DEPTH = "half",
    verbose=False
    )

# copied from globals
DEFAULT_LODS = globals.DEFAULT_LODS
OIIO_DATATYPES = globals.OIIO_DATATYPES

## MULTITHREADED ##
def processTexture(input_texture, **options):
    """ Process the texture with OpenImageIO. """
    spam=''
    startdir=options.get('startdir', '')
    output_name=options.get('output_name', '') # output_name = ASSET_tex_src/ASSET_chan_1001.exr ( file name - rootdir )
    mipfilter=options.get('mipfilter', 'box')
    asset=options.get('asset')
    srgb_full=options.get('srgb_full', False)
    
    processTotal=options.get('totaltex')
    processIndex=options.get('processIndex')    
    
    # FORMAT THE OUTPUT
    job_output=dict()
    myResult=dict()

    if 'mipmap_formats' in options.keys():
        mipmap_formats=options.get('mipmap_formats')
    
    subimages=False
    if 'subimage_formats' in options.keys():
        subimage_formats=options.get('subimage_formats')
        subimages=True
       
    palette=''
    if 'palette' in options.keys():
        palette=options.get('palette')

    noncolor=''
    if 'noncolor' in options.keys():
        noncolor=options.get('noncolor')

    colorspace=''
    if 'colorspace' in options.keys():
        colorspace=options.get('colorspace')

    if colorspace.lower() not in 'srgb linear'.split():
        colorspace='sRGB'

    textype=''
    if 'textype' in options.keys():
        textype=options.get('textype')

    
    if not mipmap_formats:
        return ConversionError('please specify at least one mipmap file format (exr, tx or rat). Check your TextureManager preferences')
    
    # force the colorspace to sRGB if noncolor is passed
    if noncolor:
        colorspace='sRGB'
        
    # DEBUG
    """
    print '\n>> Mip-map  formats: ', ', '.join(mipmap_formats)
    print '>> subimage formats: ', ', '.join(subimage_formats)
    print '>> mipmap filter: ', mipfilter
    """    
      
    procList = ['0', '1', '4', '8']
    output, err = runCommand('grep processor /proc/cpuinfo')
    numprocs = int(output.count('processor'))
    
    #print '\n>> Colorspace: %s' % colorspace
    #print '>> CPU Cores: ', numprocs
    
    if os.path.exists(input_texture):
        if oiioCheck:
            path, fn=os.path.split(input_texture)
            bn, fileext=os.path.splitext(fn)
            
            # IF THE USER HAS RENAMED THE TEXTURE...
            if output_name:
                fn=os.path.split(output_name)[-1]
                bn, fileext=os.path.splitext(fn)
            
            imageinfo=detailedInfo(input_texture)
            
            try:
                xres, yres=imageinfo.get('resolution')
            except:
                xres = 0
                yres = 0
                logger.getLogger().warning('cannot determine resolution for file "%s", please check that it is readable' % input_texture)
                spam+='\nWARNING: cannot determine resolution for file "%s", please check that it is readable' % input_texture
            
            # DON'T OUTPUT SUBIMAGES FOR IMAGES LESS THAN 64 PIXELS
            if int(xres)<64:
                if subimages:
                    subimages=False
            
            # BIT DEPTH
            is8Bit=False
            if imageinfo.get('depth')=='8-bit integer':
                is8Bit=True
            
            result=dict()
            job_errors=[]
            lods=getImageScales(int(xres))

            headers=dict()
            now = datetime.datetime.now()
            date=now.strftime("%Y-%m-%d-%H-%M")
            
            headers.update(
                   sourcefile=input_texture,
                   artist=os.environ.get('USER'),
                   date=date,
                   show=os.environ.get('SHOW'),
                   shot=os.environ.get('SHOT'),
                   palette=palette,
                   asset=asset,
                   noncolor=noncolor,
                   channel=textype,
                   colorSpace=colorspace,
            )
            
            # TAG FOR THE COLORSPACE THAT GETS WRITTEN INTO THE HEADERS
            colorspace_header='sRGB'            
            tstart = time.time()

            total_img=0
            src_file = ''
            tmpfile = ''
            fullres_exr = ''
            
            # GENERATE THE FULLRES EXR
            fullres_path=os.path.join(startdir, '%s_tex_fullres' % asset.upper())
            src_path=os.path.join(startdir, '%s_tex_src' % asset.upper())
            
            mkdirPath(fullres_path)
            mkdirPath(src_path)
            
            # CREATE THE SOURCE FILE IN THE USER SRC DIR
            src_file=os.path.join(src_path, fn)
            #copy_cmd='oiiotool %s --tile 64 64 -o %s' % (input_texture, src_file)  # TILED ISN'T COOL - MARI CANNOT REIMPORT        
            copy_cmd='oiiotool %s -o %s' % (input_texture, src_file)
            srcCopy = subprocess.Popen(copy_cmd, stdout=subprocess.PIPE, shell=True)
            out,err = srcCopy.communicate()
            if not srcCopy.wait():                    
                if err:
                    spam+=err

                if processIndex:
                    msg= '*'* (33 + len(src_file))
                    if not processTotal:
                        processTotal=1
                    spam+=('\n%s\nCOPYING TO SOURCE: %s (%d of %d) \n%s\n' % (msg, src_file, processIndex, processTotal, msg))
                else:
                    msg= '*'* (22 + len(src_file))
                    spam+=('\n%s\nCOPYING TO SOURCE: %s\n%s\n' % (msg, src_file, msg))

                myResult.update({'input_texture':input_texture})
                myResult.update({'source':src_file})
                
                tmpFullExr=os.path.join(fullres_path, '%s_tmp.exr' % bn)
                fullres_exr=os.path.join(fullres_path, '%s.exr' % bn)
                fullres_tx=os.path.join(fullres_path, '%s.tx' % bn)
                fullres_rat=os.path.join(fullres_path, '%s.rat' % bn)
                
                fullres_exr_cmd = ''
                fullres_tx_cmd  = ''
                
                if noncolor:
                    spam+=('\n  >> Data Type: non-color ( %s )' % imageinfo.get('depth'))
                    if is8Bit:
                        spam+=('\n  >> converting 8-bit to half')
                        fullres_exr_cmd='oiio_maketx %s --threads 0 --hash --filter %s --oiio --tile 64 64 -d half -o %s' % (src_file, mipfilter, fullres_exr)
                        fullres_tx_cmd= 'oiio_maketx %s --threads 0 --hash --filter %s --oiio --tile 64 64 -d half -o %s' % (src_file, mipfilter, fullres_tx)
                        #fullres_exr_cmd='oiio_maketx %s --threads %d --hash --tile 64 64 -d half -o %s' % (src_file, numprocs, fullres_exr)
                        #fullres_tx_cmd= 'oiio_maketx %s --threads %d --hash --tile 64 64 -d half -o %s' % (src_file, numprocs, fullres_tx)

                    else:
                        fullres_exr_cmd='oiio_maketx %s --threads 0 --hash --filter %s --oiio --tile 64 64 -o %s' % (src_file, mipfilter, fullres_exr)
                        fullres_tx_cmd= 'oiio_maketx %s --threads 0 --hash --filter %s --oiio --tile 64 64 -o %s' % (src_file, mipfilter, fullres_tx)
                        #fullres_exr_cmd='oiio_maketx %s --threads %d --hash --tile 64 64 -o %s' % (src_file, numprocs, fullres_exr)
                        #fullres_tx_cmd= 'oiio_maketx %s --threads %d --hash --tile 64 64 -o %s' % (src_file, numprocs, fullres_tx)

                else:
                    # ASSUME COLORSPACE IS ALWAYS INITIALLY SRGB
                    if not colorspace:
                        colorspace='sRGB'
                        colorspace_header='sRGB'

                    if colorspace.lower()=='srgb':
                        spam+=('\n  >> Data Type: color ( %s )' % imageinfo.get('depth'))
                        if not srgb_full:
                            spam+=('\n  >> converting to Linear')    
                            ### assume input images ARE sRGB already -- don't apply sRGB tonal curve twice
                            fullres_exr_cmd='oiio_maketx %s --threads 0 --hash --filter %s --oiio --colorconvert sRGB linear --tile 64 64 -d half -o %s' % (src_file, mipfilter, fullres_exr)
                            fullres_tx_cmd= 'oiio_maketx %s --threads 0 --hash --filter %s --oiio --colorconvert sRGB linear --tile 64 64 -d half -o %s' % (src_file, mipfilter, fullres_tx)
                            #fullres_exr_cmd='oiio_maketx %s --threads %d --hash --colorconvert sRGB linear --tile 64 64 -d half -o %s' % (src_file, numprocs, fullres_exr)
                            #fullres_tx_cmd= 'oiio_maketx %s --threads %d --hash --colorconvert sRGB linear --tile 64 64 -d half -o %s' % (src_file, numprocs, fullres_tx)
                            
                            colorspace_header='Linear'
                        else:
                            spam+=('\n  >> *** forcing sRGB ***')    
                            ### assume input images ARE sRGB already -- don't apply sRGB tonal curve twice
                            fullres_exr_cmd='oiio_maketx %s --threads 0 --hash --filter %s --oiio --tile 64 64 -d half -o %s' % (src_file, mipfilter, fullres_exr)
                            fullres_tx_cmd= 'oiio_maketx %s --threads 0 --hash --filter %s --oiio --tile 64 64 -d half -o %s' % (src_file, mipfilter, fullres_tx)
                            colorspace_header='sRGB'
                    
                    # TEXTURE IS TAGGED AS LINEAR
                    if colorspace.lower()=='linear':
                        if not srgb_full:
                            #sspam+=('\n  >> Data Type: color ( %s )' % imageinfo.get('depth'))
                            fullres_exr_cmd='oiio_maketx %s --threads 0 --hash --filter %s --oiio --tile 64 64 -d half -o %s' % (src_file, mipfilter, fullres_exr) # added "--tile 64 64 -d half"
                            fullres_tx_cmd= 'oiio_maketx %s --threads 0 --hash --filter %s --oiio --tile 64 64 -d half -o %s' % (src_file, mipfilter, fullres_tx)  # added "--tile 64 64 -d half"
                            colorspace_header='Linear'
                        else:
                            spam+=('\n  >> *** forcing conversion to sRGB ***')  
                            fullres_exr_cmd='oiio_maketx %s --threads 0 --hash --filter %s --oiio --colorconvert linear sRGB --tile 64 64 -d half -o %s' % (src_file, mipfilter, fullres_exr)
                            fullres_tx_cmd= 'oiio_maketx %s --threads 0 --hash --filter %s --oiio --colorconvert linear sRGB --tile 64 64 -d half -o %s' % (src_file, mipfilter, fullres_tx)
                            colorspace_header='sRGB'
                
                spam+=('\n  >> resolution: %d x %d' % (int(xres), int(yres)))
                if os.path.exists(src_file):
                    if 'exr' in mipmap_formats:
                        fullres_exr_sp = subprocess.Popen(fullres_exr_cmd, stdout=subprocess.PIPE, shell=True)
                        frout, frerr = fullres_exr_sp.communicate()

                        # wait on the fullres_exr, everything below this relies on it
                        if not fullres_exr_sp.wait():
                            if frerr:
                                spam+=frerr
                            
                            if os.path.exists(fullres_exr):
                                # UPDATE THE HEADERS
                                headers.update(colorspace=colorspace_header)
                                
                                #print json.dumps(headers, indent=5)
                                try:         
                                    writeHeadersInplace(fullres_exr, **headers)
                                except:
                                    logger.getLogger().warning('headers could not be written for: "%s", image may be corrupted' % fullres_exr) 
                                spam+=('\n  >> outputting fullres exr: "%s"' %  fullres_exr)
                                myResult.update({'fullres_exr':fullres_exr})
                                total_img+=1


                                if 'tx' in mipmap_formats:
                                    fullres_tx_sp = subprocess.Popen(fullres_tx_cmd, stdout=subprocess.PIPE, shell=True)
                                    frout, frerr = fullres_tx_sp.communicate()
                                    while not fullres_tx_sp.wait():
                                        
                                        if os.path.exists(fullres_tx):
                                            spam+=('\n  >> outputting fullres tx:  "%s"' %  fullres_tx)
                                            myResult.update({'fullres_tx':fullres_tx})
                                            total_img+=1
                                        else:
                                            spam+=('\n >> ERROR: texture "%s" could not be converted' %  fullres_tx)
                                            job_errors.append('texture "%s" could not be converted' %  fullres_tx)
                                
                                # HOUDINI RAT
                                if 'rat' in mipmap_formats:
                                    spam+=('\n  >> outputting fullres rat: "%s"' % (fullres_rat))
                                    fullresRat=imageToRat(fullres_exr, fullres_rat, **ratDefaults)
                                    if os.path.exists(fullres_rat):
                                        myResult.update({'fullres_rat':fullres_rat})
                                        total_img+=1
                                    else:
                                        spam+=('\n  >> ERROR: texture "%s" could not be converted' %  fullres_rat)
                                        job_errors.append('texture "%s" could not be converted' %  fullres_rat)

                                # SUBIMAGES
                                subimage=1                            
                                
                                if subimages:
                                    lods=['high', 'medium', 'low', 'tiny']
                    
                                    for lod in lods:                    
                                        attrs=DEFAULT_LODS.get(lod)
                                        lod_formats = attrs.get('formats')                    
                                        lod_abbr = attrs.get('abbreviation')
                                        
                                        
                                        if subimage_formats:
                                            # resolution loop
                                            spam+=('\n\n## Processing resolution: "%s":' % lod.upper())
                                            result[lod]=dict()
                                            curpath=os.path.join(startdir, '%s_tex_%sres' % (asset, lod_abbr))
                                            if not os.path.exists(curpath):
                                                spam+=('\n  >> creating directory: %s' % curpath)
                                                mkdirPath(curpath)
                                                
                                            result.get(lod).update(path=curpath)                                    
                                        
                                            # LOOP THROUGH FORMATS HERE
                                            if srgb_full:
                                                # SOURCE EXR IS NOT LINEAR, DO NOT CONVERT TO SRGB
                                                cmd='oiiotool %s --selectmip %d -d unit16' % (fullres_exr, subimage)
                                            else:
                                                cmd='oiiotool %s --selectmip %d -d unit16 --colorconvert linear sRGB' % (fullres_exr, subimage)
                                                                         
                                            for format in subimage_formats:
                                                outfile = os.path.join(curpath, '%s.%s' % (bn, format))
                                                
                                                if format in 'png tif tiff'.split():
                                                    cmd+=' -o %s -d half ' % outfile
                                                    
                                                elif format == 'exr':
                                                    cmd+=' -o %s ' % outfile                                    
                                                else:
                                                    continue
                    
                                                myResult.update({'%sres_%s' % (lod_abbr, format):outfile})
                                                hstr=__pickle(headers)
                    
                                                # CREATE THE IMAGE
                                                os.system(cmd)
                                                if os.path.exists(outfile):
                                                    spam+=('\n  >> outputting "%s" texture: "%s"' % ('%sres_%s' % (lod_abbr, format), outfile))
                                                    headers.update(colorSpace='sRGB')
                                                    writeHeadersInplace(outfile, **headers) 
                                                    total_img+=1
        
                                            # TODO: FIGURE OUT IF THIS IS IN THE RIGHT PLACE IN THREADED MODE
                                            subimage+=1

                            else:
                                spam+=('\n  >> ERROR: texture "%s" could not be converted' %  fullres_exr)
                                job_errors.append('texture "%s" could not be converted' %  fullres_exr)

                    tend = time.time()
                    readTime, tstart = tend - tstart, tend
                    readMin = '%1.2f' % (float(readTime) / 60.0)
                    spam+=('\n\t\n...%d images converted for "%s" in: %1.2f seconds (%s minutes)\n' %  (total_img, fn, readTime, readMin))
                    
                    #UPDATE THE MANAGER WITH ALL OF THE OUTPUT
                    if job_errors:
                        myResult.update(errors=job_errors)
                        sendErrorEmail(job_errors, subject='XConvert error')
                    myResult.update(spam=spam)
                    myResult.update(imagesConverted=total_img)
                    job_output[str(processIndex)]=myResult
                    # job_result gets added to the _output attribute
                    return job_output
                
                # ERRORS
                else:
                    # SOURCE TEXTURE COPY FAILED
                    return OIIOError('Source texture copy failed: %s' % src_file)
                    
            else:
                return OIIOError('texture "%s" could not be converted, texture may be corrupt' % input_texture)
                        
        else:
            return OIIOError('oiio is not available, aborting')
    else:
        return OIIOError('Input texture %s does not exist, aborting' % input_texture)

# DEPRECATED
def createTempImage(filename, outputdir):
    """
    Create a temp copy of the texture, to add metadata to
    """
    if os.path.exists(filename):
        import shutil
        path, fn=os.path.split(filename)
        bn, fileext=os.path.splitext(fn)
        newfile=os.path.join(outputdir, '%s-TMP%s' % (bn, fileext))
        return newfile
    else:
        return

def getMipMapLevels(**info):
    return tuple([int(x.split('x')[0]) for x in info.get('mipmap levels')])

def clearHeaders(inputfile):
    """
    Clears metadata from the file texture
    """
    if os.path.exists(inputfile):
        fileext=os.path.splitext(os.path.split(inputfile)[-1])[-1]
        attrStr=''
        if fileext.lower() in ['.tif', '.tiff', '.jpg', '.jpeg', '.dpx']:
            clear_cmd="oiio_iconvert --inplace --clear-keywords %s" % inputfile
            output, error=runCommand(clear_cmd)

        elif fileext.lower() in ['.exr']:
            fileIn=OpenEXR.InputFile(inputfile)
            header=fileIn.header()
            for k in header.keys():
                if 'mrx:' in k:
                    header.pop(k)

            oldChannels = header["channels"].keys()
            newChannels = dict(zip(oldChannels, fileIn.channels(oldChannels)))
            fileIn.close()

            fileOut = OpenEXR.OutputFile(inputfile, header)
            fileOut.writePixels(newChannels)
            fileOut.close()

def writeHeadersInplace(inputfile, clear=True, **options):
    if os.path.exists(inputfile):
        fileext=os.path.splitext(os.path.split(inputfile)[-1])[-1]
        attrStr=''
        #result+=" --attrib mrx:%s %s" % (attr, val)
        if fileext.lower() not in ['.tif', '.tiff', '.jpg', '.jpeg', '.dpx']:
            attrStr=__pickle(options)

        else:
            attrStr=__pickle(options, tif=True) 
            if clear:
                clear_cmd="oiio_iconvert --inplace --clear-keywords %s" % inputfile
                output, error=runCommand(clear_cmd)       
        cmd="oiio_iconvert --inplace %s %s" % (r'%s' % attrStr, inputfile)
        #oiiotool /X/pathtofile/myfile.tif  --keyword "mrx:attr val" -o /tmp/myfile.tif
        output, error=runCommand(cmd, kwd=True)

# DEPRECATED
def writeHeaders(inputfile, outputfile='', **options):
    """
    Writes arbitrary metadata into the output image
    """
    inplace=False
    if not outputfile:
        outputfile=createTempImage(inputfile, '/tmp')
        if os.path.exists(outputfile):
            inplace=True
    fileext=os.path.splitext(os.path.split(outputfile)[-1])[-1]
    attrStr=''
    if fileext.lower() not in ['.tif', '.tiff', '.jpg', '.jpeg', '.dpx']:
        attrStr=__pickle(options)
    else:
        attrStr=__pickle(options, tif=True)
    cmd="oiiotool %s %s -o %s" % (inputfile, r'%s' % attrStr, outputfile )
    output, error=runCommand(cmd)
    #oiiotool /X/pathtofile/myfile.tif  --keyword "mrx:attr val" -o /tmp/myfile.tif 
    if not options.get('verbose'):
        for o in [output, error]:
            print o
    if inplace:
        try:
            shutil.copy(outputfile, inputfile)
            outputfile=inputfile
        except:
            print 'ERROR: image write failed'
            return
    return outputfile
        
def readHeaders(filename):
    """ Read headers from the specified file """
    result=dict()
    if os.path.exists(filename):
        #logger.getLogger().debug('reading headers from texture: %s' % filename)
        fileext=os.path.splitext(os.path.split(filename)[-1])[-1]
        cmd='oiio_iinfo -v -a %s' % filename
        output, error=runCommand(cmd)
        data=output.split('\n')
        data.pop(0)
        if fileext.lower() not in ['.tif', '.tiff', '.jpg', '.jpeg', '.dpx']:
            for d in data:
                if 'mrx:' in d:
                    kmatch=re.search('mrx:(?P<key>\w+):(?P<val>.*)$', d)
                    if kmatch:
                        k=kmatch.group('key')                        
                        try:
                            v=json.loads(kmatch.group('val'))
                            result[k]=v
                        except:
                            pass
        else:
            for d in data:
                d=d.strip()
                if 'Keywords' in d:
                    try:
                        result=__unpickle(d)
                    except:
                        pass
    return result
     
def addHeaders(inputfile, **options):
    """
    Adds arbitrary metadata into the input image
    """
    if os.path.exists(inputfile):
        existing_headers=readHeaders(inputfile)
        for attr, val in options.iteritems():
            existing_headers.update({attr:val})
        try:
            writeHeadersInplace(inputfile, **existing_headers)
        except:
            pass

def __unpickle(attr):
    result=dict()
    data=re.sub('Keywords: ', '', attr.strip())
    dataList=[re.sub('"', '', o.strip()) for o in data.split(';')]
    for d in dataList:
        k, v=d.split()
        k=re.sub('mrx:', '', k)
        result[k]=v
    return result

def __pickle( attrs, tif=False):
    result=''
    for attr, val in attrs.iteritems():
        if val:
            if not tif:
                result+=" --attrib mrx:%s %s" % (attr, val)
                
            else:
                result+=' --keyword "mrx:%s %s"' % (attr, val)
    return result


def iinfo(filename):
    """
    Gets image info
    """   
    output, err=runCommand('oiio_iinfo %s' % filename)
    return formatInfo(output, filename)


# working - see xiinfo.fileInfo()
def formatInfo(output, inputfile, verbose=False):
    """
    gets basic file information about a texture
    """
    if verbose:
        print 'formatInfo:   ', __file__
    result = dict()
    try:
        #output=re.sub(inputfile, '', output)
        #filename=inputfile
        filename, data = output.split(':')
        #if filename.strip()!=inputfile:
            #print 'error, filename should be %s (%s)' % (inputfile, filename)
        #data = output.split(':')        
        if verbose:
            print output
        data = data.split(',')
        result.update(filename=filename.strip())    
        for d in data:
            d = re.sub('\n$', '', d)
            d = re.sub(' \(\+mipmap\)', '',  d)
            #data=formatResolution(expr.group('resolution'))
            resmatch = re.search('(\d+)x(\d+)', re.sub(' ', '', d))              
            if resmatch:
                result.update(resolution=resmatch.groups())            
            elif 'channel' in d:
                channel = re.sub('channel', '', d)
                channel = "".join(channel.split())
                result.update(channels=channel)
            else:
                for image_format in ['tiff', 'png', 'openexr', 'jpg', 'rat']:
                    if image_format in d:
                        #print 'depth string: ', d
                        d = d.strip()
                        depth, image_format = d.split(' ')
                        if '/' in depth:
                            depthData = formatChannelData(inputfile, depth) 
                            depth = d.split('/')[0]
                            result.update(channels=depthData)

                        if depth in OIIO_DATATYPES.keys():
                            depth = OIIO_DATATYPES.get(depth)
                        result.update(depth=depth)
                        if image_format != 'openexr':
                            image_format = image_format.upper()
                        else:
                            image_format = 'OpenEXR'
                        result.update(format=image_format)
    except Exception, err:
        #logger.getLogger().warning('xconvert.formatInfo: %s' % err)
        result.update(filename=inputfile)
        
    return result


def formatChannelData(inputfile, data):
    """
    Formats multichannel EXR data
    """
    exrInput = OpenEXR.InputFile(inputfile)
    headers = exrInput.header()    
    channels = headers['channels'].keys()
    chanInfo = dict(zip(channels, data.split('/')))
    return chanInfo

def detailedInfo(filename, verbose=False):
    """
    More detailed image info
    """
    if verbose:
        print 'detailedInfo: ', __file__
        
    result=dict()
    if os.path.exists(filename):
        output, err=runCommand('oiio_iinfo -v %s' % filename)
        if verbose:
            print output
        data=output.split('\n')
        result=dict()
        
        # the first line of the output is always the basic file attributes, so lets pop it and format it
        basicInfo=formatInfo(data.pop(0), filename, verbose=verbose)
        result.update(**basicInfo)
        detailed_info=iinfo_detailed(data)
        result.update(**detailed_info)

        try:
            for attr, val in basicInfo.iteritems():
                result[attr]=val
        except:
            pass
        for d in data:
            try:
                x=d.split(':')
                if len(x) is 2:
                    k, v = x[0], x[1]
                if len(x) is 3:
                    k, v = x[1], x[2]
                
                key=k.strip()
                v=re.sub('\"', '', v.strip())
                if key in ['MIP-map levels', 'channel list', 'tile size', 'textureformat', 'compression', 'Software', 'DateTime', 'ColorSpace']:
                    if key=='MIP-map levels':
                        key='mipmap levels'
                        v=tuple(v.split())
                    elif key=='channel list':
                        key='channel'
                    elif key=='ColorSpace':
                        key='colorspace'
                        if v=='65535':
                            v='Adobe RGB'
                    else:
                        key=key.lower()
    
                    result[key]=v
            except Exception, err:
                pass
            
    # MUDBOX SUBSTITUTION
    if result.get('channels')=='1':
        if result.get('channel')=='R':
            result.update(mudbox=True, displacement=True)
    return result

def iinfo_detailed(output, verbose=False):
    """
    More detailed image info
    """
    result=dict()
    for op in output:
        try:
            k, v=op.split(':')
            key=k.strip()
            v=re.sub('\"', '', v.strip())
            if key in ['MIP-map levels', 'channel list', 'tile size', 'textureformat', 'compression', 'Software', 'DateTime']:
                if key=='MIP-map levels':
                    key='mipmap levels'
                    v=tuple(v.split())
                elif key=='channel list':
                    key='channel'
                else:
                    key=key.lower()

                result[key]=v
        except:
            pass
    return result

# Texturizer-specific
def getImageScales(n, lods=('fullres', 'hires', 'midres', 'lores', 'tinyres')):
    """
    Returns the power of two resolutions, given n=image resolution
    """
    result=dict()
    for i in range(0, len(lods)):
        if lods[i]=='full':
            result[lods[i]]=n
        else:
            n=n/2
            try:
                result[lods[i]]=int(pow(2, int(log(n, 2) + 0.5)))
            except:
                result[lods[i]]=n
    return result

# Texturizer-specific
def getImageScale(filename, lodres):
    """
    returns the image scale as a percentage
    """
    imageinfo=iinfo(filename)
    xres, yres = imageinfo.get('resolution')

    rmin = float(min(xres, yres))
    rmax = float(max(xres, yres))
    dmin = lodres.get('resolution')
    
    # if the current resolution is full, just return the current image resolution
    if lodres == 'full':
        dmin = rmax
    scale = min(1.0, dmin/rmax)

    if int(scale*rmin) < dmin:
        scale *= dmin/rmin

    if scale > 1.0:
        scale = 1.0

    return float("%.4f" % scale)

def imageToRat( inputfile, outputfile, **options):
    """ Converts an image to houdini RAT """
    rat_cmd = ICONVERT
    rat_cmd = '%s -d half ' % rat_cmd
    rat_cmd = '%s %s %s' % (rat_cmd, inputfile, outputfile)        
    rat_convert = subprocess.Popen(rat_cmd, stdout=subprocess.PIPE, shell=True)
    if not rat_convert.wait():    
        if os.path.exists(outputfile):
            return outputfile
    else:
        return
 
def mkdirPath(path):
    import errno
    try:
        os.makedirs(path)
    except os.error, e:
        if e.errno != errno.EEXIST:
            raise

def rmDir(path):
    import shutil
    try:
        shutil.rmtree(path)
    except Exception, err:
        print err

def isList(item):
    """
    Returns true if the argument is a list
    """
    retval = False
    if type(item) in (ListType, TupleType) :
        retval = True

def runCommand(cmd, stdin=None, env=None, kwd=False):
    """
    Runs a command-line command
    """
    if not isList(cmd):
        if kwd:
            cmd = commandStr(cmd)
        else:
            cmd = cmd.split()
    """
    rcmd = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    output ,err = rcmd.communicate()
    rcmd.wait()
    return output, err
    """
    opts = dict(stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if env:
        opts.update(env=env)
    if stdin:
        opts.update(stdin=subprocess.PIPE)
        stdout, stderr=subprocess.Popen(cmd, **opts).communicate(stdin)
    else :
        stdout, stderr=subprocess.Popen(cmd, **opts).communicate()
    return stdout, stderr    

# TODO: fix this
def commandStr(cmd):
    cmdsout=[]
    cmds=cmd.split()
    for i in range(0, len(cmds)):
        out=cmds[i]
        if cmds[i].startswith('"'):
            out='%s %s' % (cmds[i], cmds[i+1])
        elif cmds[i].endswith('"'):
            continue
        cmdsout.append(re.sub('"', '', out))
    return cmdsout

def oiioCheck():
    retval=False
    try:
        output, error=runCommand('oiiotool --help')
        if output:
            retval=True
    except:
        pass
    return retval

def myShit():
    return 'fuck off'

def newIINFO(filename):
    iinfo = subprocess.Popen('oiio_iinfo -v %s' % filename, stdout=subprocess.PIPE, shell=True)
    out,err = iinfo.communicate()

    exclude_strings = ['xmpMM',]
    data=dict()
    basicInfo=''
    idx=0
    for line in out.split('\n'):
        if not idx:
            data.update(formatBasicInfo(line))

        idx+=1
        line=line.strip()
        if 'software' in line.lower():
            if 'software' not in data.keys():
                val=re.sub('Software: ', '', line).strip().split()[0]

                data.update(software=val)
        if 'colorspace' in line.lower():
            if 'oiio:ColorSpace:' in line:
                if 'ColorSpace' not in data.keys():
                    val=re.sub('oiio:ColorSpace:', '', line).strip()
                    val=re.sub('"', '', val)
                    data.update(ColorSpace=val)
                    continue
            elif 'Exif:ColorSpace:' in line:
                if 'ColorSpace' not in data.keys():
                    val=re.sub('Exif:ColorSpace:', '', line).strip()
                    val=re.sub('"', '', val)
                    data.update(ColorSpace=val)
    return data

def formatBasicInfo(basicInfo):
    """
    parses the basicInfo (first) line from oiio_iinfo
    """
    data=dict()
    filename, attrs=basicInfo.split(':')
    attrs=attrs.split(',')
    for attr in attrs:
        if 'x' in attr:
            #attr=attrs.pop(attrs.index(attr))
            val=tuple([x.strip() for x in attr.split('x')])
            data.update(resolution=val)
            
        elif 'channel' in attr:
            #attr=attrs.pop(attrs.index(attr))
            attr=re.sub('channel', '', attr)
            data.update(channels=attr.strip())
        
        else:
            for x in globals.OIIO_DATATYPES.keys():
                if x in attr:
                    depth, format=attr.split()
                    if depth:
                        try:
                            data.update(depth=globals.OIIO_DATATYPES.get(depth.strip()))
                        except:
                            data.update(depth=depth.strip())
                    if format:
                        data.update(format=format.strip())
    return data

class OIIOError(Exception): pass

class ConversionError(Exception): pass

def sendErrorEmail(msg, subject='XConvert error', func='procesTexture', **kwargs):
    """
    Sends an email to tools when something doesn't go right
    """
    from .. import xmail    
    if type(msg) is list:
        msg = '\n'.join(msg)
    show=os.getenv('SHOW')
    shot=os.getenv('SHOT')
    user=os.getenv('USER')
    jobID='00000'
    try:
        jobID=os.getenv('JOB_ID')
    except:
        pass
    host='unkown host'
    try:
        host=os.getenv('HOSTNAME')
    except:
        pass

    date=time.asctime( time.localtime(time.time()) )
    body_text="""
Show:  %s
Shot:  %s
User:  %s
Date:  %s
Host:  %s
JobID: %s

%s had an error:

%s
    
    
    """ % (show, shot, user, date, host, jobID, func, str(msg))
    
    xmail.send_mail('%s@mrxfx.com' % user, ['michaelf@mrxfx.com'], '[TextureManager] %s' % subject, body_text, server="mail.mrxfx.com")