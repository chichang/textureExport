
import os
import mari
import multiprocessing
import xconvert as xc
reload(xc)
import xgUtils as imp_utils
reload(imp_utils)

#======================================================================
#	UTIL
#======================================================================
su = imp_utils.ccSysUtil()


class TextureConverter(multiprocessing.Process):
	#exporter
    def __init__(self, task_queue):
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue

    def run(self):
        proc_name = self.name
        while True:

            next_task = self.task_queue.get()

            # kill the thread when the task is 'None'
            if next_task is None:
                self.task_queue.task_done()
                #print '%s: exiting...' % proc_name
                break
            #print '%s: exporting textures...' % proc_name
            #run __call__
            #result = next_task()
            next_task()
            self.task_queue.task_done()

        return

class TextureConvertTask():
    '''
    task object for the exportor to call.
    '''
    def __init__(self, imagePath, format, ncd):
        self.imagePath = imagePath
        self.format = format
        self.ncd = ncd
        self.exrExportStr = os.path.join(os.path.split(imagePath)[0], os.path.splitext(os.path.split(imagePath)[1])[0] + ".exr")

    def __call__(self):

		#if exr do mipmap
		print "processing textures ..."

		if self.format == "exr": 

			#local convert mipmap exr
			if self.ncd == False:
				callString = "oiio_maketx " + str(self.imagePath) + " --colorconvert sRGB linear --tile 64 64 --hash -o " + str(self.imagePath)

			elif self.ncd == True:
				callString = "oiio_maketx " + str(self.imagePath) + " --tile 64 64 --hash -o " + str(self.imagePath)

			su.runCommand(callString)

			#mrx headers
			#xc.writeHeadersInplace(self.imagePath, artist = xUserName, asset = xAsset, show = xShow)
			if self.ncd == False:
				xc.writeHeadersInplace(self.imagePath, colorSpace = "linear")
			else:
				xc.writeHeadersInplace(self.imagePath, colorSpace = "ncd")


		elif self.format == "tif":

			#local convert mipmap exr
			if self.ncd == False:
				callString = "oiio_maketx " + str(self.imagePath) + " --colorconvert sRGB linear --tile 64 64 --hash -o " + str(self.exrExportStr)

			elif self.ncd == True:
				callString = "oiio_maketx " + str(self.imagePath) + " --tile 64 64 --hash -o " + str(self.exrExportStr)

			su.runCommand(callString)

			#mrx headers
			#xc.writeHeadersInplace(exportStr, artist = xUserName, asset = xAsset, show = xShow)
			if self.ncd == False:
				xc.writeHeadersInplace(self.exrExportStr, colorSpace = "linear")
			else:
				xc.writeHeadersInplace(self.exrExportStr, colorSpace = "ncd")



def processTextures(textureList, imageFormat, maxCpu):
	'''
	function called in main exoprter.
	'''
	cpu_count = multiprocessing.cpu_count()

	# MAX CPUS
	if cpu_count>maxCpu:
		cpu_count=maxCpu

	tasks = multiprocessing.JoinableQueue()

	exporters = [ TextureConverter(tasks) for i in range(cpu_count) ]

	for key in textureList.keys():
		print "adding task: ", key
		tasks.put(TextureConvertTask(imagePath = key, format=imageFormat, ncd=textureList[key]))
		mari.app.processEvents()

	# send the signal to terminate all jobs
	for i in xrange(cpu_count):
		tasks.put(None)
		print "adding None s ..."
		mari.app.processEvents()

	for w in exporters:
		w.start()
		print "starting: ", w.name
		mari.app.processEvents()

	# Wait for all of the tasks to finish
	tasks.join()





def initializeJobScripts(self):
    """
    Gets the template scripts
    """
    import re
    result = dict()
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    result.update(submitTextureJob=os.path.join(template_dir, 'submitTextureJob.template.py'))
    result.update(makeTextures=os.path.join(template_dir, 'makeTextures.template.py'))
    result.update(publishTextures=os.path.join(template_dir, 'publishTextures.template.py'))
    result.update(manualPublish=os.path.join(template_dir, 'manualPublish.template.py'))
    return result