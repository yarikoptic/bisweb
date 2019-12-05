#!/usr/bin/env python3

# LICENSE
# 
# _This file is Copyright 2018 by the Image Processing and Analysis Group (BioImage Suite Team). Dept. of Radiology & Biomedical Imaging, Yale School of Medicine._
# 
# BioImage Suite Web is licensed under the Apache License, Version 2.0 (the "License");
# 
# - you may not use this software except in compliance with the License.
# - You may obtain a copy of the License at [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)
# 
# __Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.__
# 
# ENDLICENSE

import sys
import pdb


sys.path.append('/data15/mri_group/dave_data/bisweb/src/')

try:
    import bisweb_path;
except ImportError:
    bisweb_path=0;
    


import numpy as np
import biswebpython.core.bis_basemodule as bis_basemodule
import biswebpython.core.bis_objects as bis_objects
import biswebpython.utilities.calcium_image as calcium_image;
import biswebpython.utilities.calcium_analysis as calcium_analysis;
from biswebpython.modules.linearRegistration import *


# from PIL import Image

import pdb
import sys

class calciumPreprocess(bis_basemodule.baseModule):

    def __init__(self):
        super().__init__();
        self.name='calciumPreprocess';
   
    def createDescription(self):
        return {
            "name": "Calcium Preprocess",
            "description": "Preprocesses calcium images. Top-hat filter, two-wavelength regression, then dF/F",
            "author": "Jackson Zhaoxiong Ding",
            "version": "1.0",
            "inputs": [
                {
                    "type": "image",
                    "name": "Input Image",
                    "description": "The input image (blue) to preprocess",
                    "varname": "blue",
                    "required": True
                },
                {
                    "type": "image",
                    "name": "Input Image",
                    "description": "The input image (uv) to preprocess",
                    "varname": "uv",
                    "required": False
                },
                {
                    "type": "image",
                    "name": "Input Mask",
                    "description": "The mask input",
                    "varname": "mask",
                    "required": True
                }
            ],
            "outputs": [
                {
                    "type": "image",
                    "name": "Output Image",
                    "description": "The output image",
                    "varname": "blueout",
                    "shortname": "bo",
                    "required": True,
                    "extension": ".nii.gz"
                },
                {
                    "type": "image",
                    "name": "Output Image",
                    "description": "The output image",
                    "varname": "uvout",
                    "shortname": "uo",
                    "required": True,
                    "extension": ".nii.gz"
                }
            ],
            "params": [
                {
                    "name": "Top Hat Window",
                    "description": "The number of frames for the top hat filter",
                    "type": "int",
                    "varname": "tophat",
                    "default": 300,
                    "low": 1,
                    "high": 1000
                },
                {
                    "name": "Bleach Correction",
                    "description": "Do exponential regression ('expReg') or top hat ('topHat')",
                    "type": "str",
                    "varname": "bleachtype",
                    "default": 'expReg'
                },
                {
                    "name": "Dual Channel?",
                    "description": "Is the input dual channel?",
                    "varname": "dual",
                    "type": "boolean",
                    "default": True
                },
                {
                    "name": "Rotation Angle",
                    "description": "Angle of rotation (deg), counter-clockwise",
                    "varname": "rotation",
                    "type": "float",
                    "default": 0,
                    "low": -180,
                    "high": 180
                },
                {
                    "name": "Downsample Ratio",
                    "description": "Downsample ratio. 1=same size, 0.1=smaller, 10=larger",
                    "varname": "downsample",
                    "type": "float",
                    "default": 1,
                    "low": 0,
                    "high": 10
                },
                {
                    "name": "Debug",
                    "description": "Toggles debug logging. Will also output intermediate steps (similar name to Xilin's MATLAB code)",
                    "varname": "debug",
                    "type": "boolean",
                    "default": False
                }
            ],
        }
        
    

    def computeMotionCorrection(self,image,regFrame='mean'):
        '''
        Expects an image in the form of an np array of size X x Y x T
        '''

        ipImageShape=image.shape
        numFrames=ipImageShape[2];
        opImg=np.zeros(ipImageShape)


        if (type(regFrame) == str) and (regFrame.lower() == 'mean'):
            targetFrame=np.mean(image,axis=2)
        elif (type(regFrame) == int) and (regFrame <= numFrames-1):
            targetFrame image[:,:,regFrame]
        else:
            message = '''Variable "regFrame" must be "mean" or an integer \n
            less than or equal to the number of frames'''
            raise Exception(message)


        initial=0;
        for frame in range(0,numFrames):
            extractedFrame= image[:,:,frame]

            ipRef = bis_objects.bisImage().create(targetFrame,[1,1,1,1,1],np.eye(4))
            ipTar = bis_objects.bisImage().create(extractedFrame,[1,1,1,1,1],np.eye(4))

            LinRegister=linearRegistration()

            fileSpec={ 'reference' : ipRef,                                    
                    'target' :  ipTar,
                    'initial' : initial }

   
            paramSpec={'intscale' : 1,
                'numbins' :  32,
                'levels' :   1,
                'optimization' : 'gradientdescent', # 0 hillclimb, 1 gradient descent, 2 conjugate descent
                'normalize' : True, # True? 
                'steps' : 4,
                'iterations' : 32,
                'mode' : 'rigid', # rigid
                'resolution' : 1.5,
                'return_vector' : "false",
                'metric' : 'NMI', # 1=CC 0,=SSD 3=NMI, 2=MI
                'debug' : True,
                'doreslice' : True}

        
            LinRegister.execute(fileSpec,paramSpec);
    
            initial=LinRegister.getOutputObject('output')
            resliced=LinRegister.getOutputObject('resliced')
            # append resliced.data_array



            opImg[:,:,frame]=np.squeeze(resliced.get_data())

        return opImg,targetFrame

            
    def checkTriggers(ipMovie,expectedStructure=[0,1],ipTriggerFile=None):
        
        import nibabel as nb
        import numpy as np
        from matplotlib import pyplot as plt
        from sklearn.cluster import AgglomerativeClustering

        
        meanSpace=allMovieData.mean(axis=1).mean(axis=0)
        #plt.scatter(np.arange(0,meanSpace.shape[0]),meanSpace)
        #plt.show()
        timeArr=np.arange(0,meanSpace.shape[0]/10000,1/10000)
        timeArr=np.expand_dims(timeArr,axis=1)
        meanSpace=np.expand_dims(meanSpace,axis=1)
        meanSpaceTimeArr=np.stack([meanSpace,timeArr]).squeeze()
        clustering = AgglomerativeClustering(n_clusters=2).fit(meanSpaceTimeArr.T)
        #plt.scatter(np.arange(0,meanSpace.shape[0]),meanSpace,c=clustering.labels_)
        #plt.show()

        nFrames=ipMovie.shape[2]
        nChannels=len(expectedStructure)
        exepectedSeq=np.tile(expectedStructure,nFrame/nChannels)

        clusterLabels=clustering.labels_

        if np.array_equal(expectedSeq,clusterLabels):
            pass
        else:
            raise Exception('Misaligned triggers')

        

    

    def directInvokeAlgorithm(self,vals):
        print('oooo invoking: something with vals', vals);


        # Parameters
        dualChannel = self.parseBoolean(vals['dual'])
        topHatWindow = vals['tophat']
        rotationAngle = vals['rotation']
        downsampleRatio = vals['downsample']
        bleachType = vals['bleachtype']
        debug=self.parseBoolean(vals['debug'])
        outputEveryStep = debug


        inputMovie = self.inputs['blue'].get_data()

        if outputEveryStep:
            out = bis_objects.bisImage().create(inputMovie,[1,1,1,1,1],np.eye(4))
            out.save('calcium_movie_all.nii.gz')


        blueMovie,uvMovie = calcium_image.channelSeparate(inputMovie)
        mask = self.inputs['mask'].get_data()



        if bleachType not in ['expReg','topHat']:
            raise Exception(ValueError, 'bleachType must be "expReg" or "topHat" (case sensitive)')

        blueMovieSize = blueMovie.shape
        uvMovieSize = uvMovie.shape

        if outputEveryStep:
            out = bis_objects.bisImage().create(blueMovie,[1,1,1,1,1],np.eye(4))
            out.save('calcium_blue_movie.nii.gz')
            out = bis_objects.bisImage().create(uvMovie,[1,1,1,1,1],np.eye(4))
            out.save('calcium_uv_movie.nii.gz')

        ###########################


        blueMovieMC,blueMovieRef = self.computeMotionCorrection(blueMovie)
        uvMovieMC,uvMovieRef = self.computeMotionCorrection(uvMovie)
        

        ###########################


        if outputEveryStep:
            out = bis_objects.bisImage().create(blueMovieMC,[1,1,1,1,1],np.eye(4))
            out.save('calcium_blue_movie_mc.nii.gz')
            out = bis_objects.bisImage().create(uvMovieMC,[1,1,1,1,1],np.eye(4))
            out.save('calcium_uv_movie_mc.nii.gz')

            out = bis_objects.bisImage().create(blueMovieRef,[1,1,1,1,1],np.eye(4))
            out.save('calcium_blue_movie_mcRef.nii.gz')
            out = bis_objects.bisImage().create(uvMovieRef,[1,1,1,1,1],np.eye(4))
            out.save('calcium_uv_movie_mcRef.nii.gz')
            #out = bis_objects.bisImage().create(mask,[1,1,1,1,1],np.eye(4))
            #out.save('mask.nii.gz')

                
        sys.exit()

        # Top Hat filter
        if bleachType == 'topHat':
            blueMovieFiltered,uvMovieFiltered = calcium_analysis.topHatFilter(blueMovie,uvMovie,mask)
        elif bleachType == 'expReg':
            blueMovieFiltered,uvMovieFiltered = calcium_analysis.expRegression(blueMovie,uvMovie,mask,outputEveryStep)

        if outputEveryStep:
            out = bis_objects.bisImage().create(blueMovieFiltered,[1,1,1,1,1],np.eye(4))
            out.save('calcium_blue_movie_mc_filt.nii.gz')
            out = bis_objects.bisImage().create(uvMovieFiltered,[1,1,1,1,1],np.eye(4))
            out.save('calcium_uv_movie_mc_filt.nii.gz')

        #### Two-wavelength Regression
        blueReg = calcium_analysis.twoWavelengthRegression(blueMovieFiltered,uvMovieFiltered,blueMovie,uvMovie,mask)
        
        if outputEveryStep:
            out = bis_objects.bisImage().create(blueReg.reshape(blueMovieSize),[1,1,1,1,1],np.eye(4))
            out.save('calcium_blue_movie_mc_filt_regress.nii.gz')

        #### dF/F

        #blue
        blueDFF,uvDFF = calcium_analysis.dFF(blueMovie,uvMovieFiltered,blueReg,mask)

        if outputEveryStep:
            out = bis_objects.bisImage().create(blueDFF.reshape(blueMovieSize),[1,1,1,1,1],np.eye(4))
            out.save('calcium_blue_movie_mc_filt_regress_dff.nii.gz')
            out = bis_objects.bisImage().create(uvDFF.reshape(uvMovieSize),[1,1,1,1,1],np.eye(4))
            out.save('calcium_uv_movie_mc_filt_regress_dff.nii.gz')
        
        # for memory
        blueMovie = []
        uvMovie = []
        out = bis_objects.bisImage().create(blueDFF.reshape(blueMovieSize),[1,1,1,1,1],np.eye(4))
        self.outputs['blueout']=out
        out = bis_objects.bisImage().create(uvDFF.reshape(uvMovieSize),[1,1,1,1,1],np.eye(4))
        self.outputs['uvout']=out
        

        
        
        return True

if __name__ == '__main__':
    import biswebpython.core.bis_commandline as bis_commandline;
    sys.exit(bis_commandline.loadParse(calciumPreprocess(),sys.argv,False));



    
