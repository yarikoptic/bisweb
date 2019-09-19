import numpy as np
import pdb
def topHatFilter(blueMovie,uvMovie,mask,topHat=300):
    # Mask (spatial), resize, and rotate
    # mask = np.array(Image.open('mask.tif').resize(downsampledSize, Image.BILINEAR).rotate(rotationAngle,Image.NEAREST,True))
    rotatedSize3D = blueMovie.shape
    
    # Reshape 
    blueMovie = blueMovie.reshape((blueMovie.shape[0]*blueMovie.shape[1], blueMovie.shape[2]))
    uvMovie = uvMovie.reshape((uvMovie.shape[0]*uvMovie.shape[1], uvMovie.shape[2]))
    mask = mask.reshape((mask.shape[0]*mask.shape[1]))
    mask = mask>0
    mask_indices = np.squeeze(np.argwhere(mask))

    # Creating time padding (invert time)
    bluePadding = np.concatenate([-blueMovie[mask,topHat:0:-1]+2*blueMovie[mask,0][:,np.newaxis], blueMovie[mask,:]],axis=1)
    uvPadding = np.concatenate([-uvMovie[mask,topHat:0:-1]+2*uvMovie[mask,0][:,np.newaxis], uvMovie[mask,:]],axis=1)

    # from skimage.morphology import white_tophat
    import skimage.morphology

    se = skimage.morphology.rectangle(1,topHat) #(1, x) shape important!
    blueFiltered = np.empty((mask.sum(), rotatedSize3D[2]+topHat))
    uvFiltered = np.empty((mask.sum(), rotatedSize3D[2]+topHat))
    for i in range(mask.sum()):
        blueFiltered[i,np.newaxis] = skimage.morphology.white_tophat(bluePadding[i,np.newaxis],se)
        uvFiltered[i,np.newaxis] = skimage.morphology.white_tophat(uvPadding[i,np.newaxis],se)

    blueMovieFiltered = np.zeros(blueMovie.shape)
    uvMovieFiltered = np.zeros(uvMovie.shape)

    blueMovieFiltered[mask_indices,:] = blueFiltered[:,topHat:]
    uvMovieFiltered[mask_indices,:] = uvFiltered[:,topHat:]
    

    blueMovieFiltered = blueMovieFiltered.reshape(rotatedSize3D)
    uvMovieFiltered = uvMovieFiltered.reshape(rotatedSize3D)
    return blueMovieFiltered,uvMovieFiltered

def expRegression(blueMovie,uvMovie,mask,debug):

    # Import bis_objects and drift correction script
    from biswebpython.modules.driftCorrectImage import driftCorrectImage
    import biswebpython.core.bis_objects as bis_objects
    
    driftcorr = driftCorrectImage()
    
    # Make sure we have a time dimension in the input data
    blueShape = blueMovie.shape
    uvShape = uvMovie.shape

    if (len(blueShape) == 3) and (len(uvShape) == 3):
        print('Both input images are 3D, assuming third dimension is time and reshaping')
        blueMovie=np.reshape(blueMovie,[blueShape[0],blueShape[1],1,blueShape[2]])
        uvMovie=np.reshape(uvMovie,[uvShape[0],uvShape[1],1,uvShape[2]])
    elif (len(blueShape) == 4) and (len(uvShape) == 4):
        pass
    else:
        raise Exception('Blue and UV images are not the same dimension and/or are not 3/4 dimensions')


    # Log transform input images
    blueMovieLog=np.log(1+blueMovie)
    uvMovieLog=np.log(1+uvMovie)


    # Create image objects for input to drift correction
    blueMovieDriftip = bis_objects.bisImage().create(blueMovieLog,[1,1,1,1,1],np.eye(4))
    uvMovieDriftip = bis_objects.bisImage().create(uvMovieLog,[1,1,1,1,1],np.eye(4))

    if debug:
        blueMovieDriftip.save('calcium_down_blue_movie_mc_rot_log.nii.gz')
        uvMovieDriftip.save('calcium_down_uv_movie_mc_rot_log.nii.gz')

    #pdb.set_trace()


    # Run first order drift correction on log transformed data
    driftcorr.execute({'input' : blueMovieDriftip},{'weight':0,'order':1,'demean_regressor':True})
    blueOutput=driftcorr.getOutputObject()
    driftcorr.execute({'input' : uvMovieDriftip},{'weight':0,'order':1,'demean_regressor':True})
    uvOutput=driftcorr.getOutputObject()

    if debug:
        blueOutput.save('calcium_down_blue_movie_mc_rot_log_reg.nii.gz')
        uvOutput.save('calcium_down_uv_movie_mc_rot_log_reg.nii.gz')
        

    # Exponential transform data back to normal, and remove inserted time dimension
    blueMovieRegress = np.squeeze(np.exp(blueOutput.get_data())-1)
    uvMovieRegress = np.squeeze(np.exp(uvOutput.get_data())-1)

    return blueMovieRegress, uvMovieRegress




def twoWavelengthRegression(blueMovieFiltered,uvMovieFiltered,blueMovie,uvMovie,mask):
    from scipy import linalg

    mask = mask.reshape((mask.shape[0]*mask.shape[1]))
    mask = mask>0
    mask_indices = np.squeeze(np.argwhere(mask))
    rotatedSize3D = blueMovie.shape

    blueMovie = blueMovie.reshape((blueMovie.shape[0]*blueMovie.shape[1], blueMovie.shape[2]))
    uvMovie = uvMovie.reshape((uvMovie.shape[0]*uvMovie.shape[1], uvMovie.shape[2]))
    blueMovieFiltered = blueMovieFiltered.reshape((blueMovieFiltered.shape[0]*blueMovieFiltered.shape[1], blueMovieFiltered.shape[2]))
    uvMovieFiltered = uvMovieFiltered.reshape((uvMovieFiltered.shape[0]*uvMovieFiltered.shape[1], uvMovieFiltered.shape[2]))

    blueBase = blueMovie - blueMovieFiltered
    uvBase = uvMovie - uvMovieFiltered

    blueRec = blueMovieFiltered + np.tile(blueBase.mean(axis=1)[:,np.newaxis],(1,rotatedSize3D[2]))
    uvRec = uvMovieFiltered + np.tile(uvBase.mean(axis=1)[:,np.newaxis],(1,rotatedSize3D[2]))

    beta = np.zeros((len(mask_indices)))
    blueReg = np.zeros(blueBase.shape)

    for i in range(mask.sum()):
        beta[i] = linalg.lstsq(uvRec[mask_indices[i],:][:,np.newaxis], blueRec[mask_indices[i],:][:,np.newaxis])[0][0][0]
        blueReg[mask_indices[i],:] = blueMovieFiltered[mask_indices[i],:] - beta[i]*uvMovieFiltered[mask_indices[i],:]
    return blueReg

def dFF(blueMovie,uvMovieFiltered,blueReg,mask,topHat=300):
    rotatedSize3D = blueMovie.shape
    mask = mask.reshape((mask.shape[0]*mask.shape[1]))
    mask = mask>0

    blueMovie = blueMovie.reshape((blueMovie.shape[0]*blueMovie.shape[1], blueMovie.shape[2]))
    uvMovieFiltered = uvMovieFiltered.reshape((uvMovieFiltered.shape[0]*uvMovieFiltered.shape[1], uvMovieFiltered.shape[2]))

    blueF = blueMovie[mask,topHat:].mean(axis=1)
    blueDFF = np.zeros(blueMovie.shape)
    blueDFF[mask,:] = np.divide(blueReg[mask,:],np.tile(blueF[:,np.newaxis],(1,rotatedSize3D[2])))

    #uv
    uvF = uvMovieFiltered[mask,topHat:].mean(axis=1)
    uvDFF = np.zeros(uvMovieFiltered.shape)
    uvDFF[mask,:] = np.divide(uvMovieFiltered[mask,:],np.tile(uvF[:,np.newaxis],(1,rotatedSize3D[2])))
    return blueDFF,uvDFF
