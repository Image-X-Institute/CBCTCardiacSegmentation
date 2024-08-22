# -*- coding: utf-8 -*-
"""
Created on Tue Jul 30 10:02:38 2024

@author: mgar5380
"""

#External Modules
import os
#import re
import glob
import shutil
#import pydicom
import argparse
#import numpy as np
import SimpleITK as sitk
from pathlib import Path

#from torch.cuda import is_available


from CBCTCardiacSegmentation.DicomHelper import PrepareCTData, WriteDicomStructs
from CBCTCardiacSegmentation.Registration import VolumeRegistration
from CBCTCardiacSegmentation.SegUtil import CentreImage, GenerateCardiacStructures, PadBinaryVol

from platipy.imaging.projects.nnunet.run import run_segmentation


def CreateCBCTSegmentations(CBCTDir,OutputDir='./CBCTSegmentations',SegmentationMethod='Synthetic',PlanningCTDir='',ElastixParamDir='',StructFile='',
                            ElastixRunDir = '',
                            HeartPadDistance=30,
                            KeepTempFiles=False):
    
    #Create Output Directory
    Path(OutputDir).mkdir(exist_ok=True)
    
    #Create Temporary Directory for temporary files
    TempDir = os.path.join(OutputDir,'TempDir')
    Path(TempDir).mkdir(exist_ok=True)
    
    """
    Convert Planning CT Dicom Info to Nifti Files
    """
    assert Path(PlanningCTDir).exists(), 'Planning CT directory {} does not exist'.format(PlanningCTDir)

    SegmentationOptions = ['Direct','Synthetic','Transform']

    assert SegmentationMethod in SegmentationOptions,'Segmentation Method {} does not exist. Options are Direct,Synthetic,Transform'.format(SegmentationMethod)

    if PlanningCTDir or not(SegmentationMethod == 'Direct'):
        print('Converting CT Files to Nifti Format')
        PlanningCTNiftiFile,StructNiftiDir = PrepareCTData(PlanningCTDir,OutputDir=TempDir,
                                                           StructFile=StructFile,
                                                           KeepTempFiles=KeepTempFiles)
    else:
        PlanningCTNiftiFile = ''
        StructNiftiDir = ''
    
    """
    Convert CBCT Dicom File(s) into nifti files. 
    """
    assert Path(CBCTDir).exists(), 'Planning CT directory {} does not exist'.format(CBCTDir)
    print('Converting CBCT Files to Nifti Format')
    CBCTNiftiFile,_ = PrepareCTData(CBCTDir,OutputDir=TempDir,
                                    PreviousNiftiFiles=PlanningCTNiftiFile,
                                    KeepTempFiles=KeepTempFiles)
        
    """
    Register Images to prepare for Segmentation
    """
    if not(SegmentationMethod == 'Direct'):        
        VolReg = VolumeRegistration(RegOutputDir=TempDir,ParamDir=ElastixParamDir,
                                    ElastixDir=ElastixRunDir)
    
        #Align PlanningCT Volume to CBCT Volume
        print('Initial Alignment of Planning CT File to CBCT File')
        CTImgOrigin,CTNewOrigin = CentreImage(PlanningCTNiftiFile)
        CBCTImgOrigin,CBCTNewOrigin = CentreImage(CBCTNiftiFile)
    
        #Rigid Registration
        print('Rigid Registration of Planning CT File to CBCT File')
        RigidTForm = os.path.join(TempDir,'CTToCBCT_Rigid.txt')
        VolReg.RigidDeformation(CBCTNiftiFile, PlanningCTNiftiFile, RigidTForm, DeleteVolumeFlag=False)
        
        assert Path(RigidTForm).exists(),'Error Creating Rigid Registration File'

        #Check if there is a heart structure already available
        if StructNiftiDir:
            HeartSegmentationFileOld = glob.glob(os.path.join(StructNiftiDir, '*HEART*.nii.gz'))[0]
            HeartSegmentationFile = os.path.join(TempDir, 'HeartSegmentation.mha')

            HeartImg = sitk.ReadImage(HeartSegmentationFileOld)
            HeartImg.SetOrigin(CTNewOrigin)
            sitk.WriteImage(HeartImg,HeartSegmentationFile)

        else:
            HeartSegImg = run_segmentation(sitk.ReadImage(PlanningCTNiftiFile))
            HeartSegmentationFile = os.path.join(TempDir, 'HeartSegmentation.mha')
            sitk.WriteImage(HeartSegImg['Struct_0'], HeartSegmentationFile)

        #Extend Heart Mask
        PaddedHeartFile = os.path.join(TempDir, 'PaddedHeartSegmentation.mha')
        PadBinaryVol(HeartSegmentationFile, OutputFileName=PaddedHeartFile, PadWidth=HeartPadDistance)

        #Deformable registration
        NonRigidTForm = os.path.join(TempDir, 'CTToCBCT.txt')
        VolReg.NonRigidDeformation(FixedVolume=CBCTNiftiFile,
                                   MovingVolume=PlanningCTNiftiFile,
                                   OutputFile=NonRigidTForm,
                                   MovingMask=PaddedHeartFile,
                                   FixedMask=PaddedHeartFile,
                                   InitTransform=RigidTForm,
                                   DeleteVolumeFlag=False)

        assert Path(NonRigidTForm).exists(), 'Error doing deformable registration'

    """
    Get Segmentations from the Image
    """
    print('Generating CBCT Segmentations')
    if SegmentationMethod == 'Transform':
        NonRigidTFormMask = os.path.join(TempDir, 'CTToCBCTMask.txt')
        VolReg.EditTFormFile(NonRigidTForm, NonRigidTFormMask)

        #Create Segmentations from planning CT
        CTSegmentationDir = os.path.join(TempDir,'CTSegmentations')
        Path(CTSegmentationDir).mkdir(exist_ok=True)
        GenerateCardiacStructures(PlanningCTNiftiFile, OutputDir=CTSegmentationDir)

        #Warp segmentations to match CBCT anatomy
        CTSegFiles = glob.glob(os.path.join(CTSegmentationDir, '*.nii.gz'))
        SubstructureOutputDir = os.path.join(OutputDir, 'OutputSegmentations_Nifti')
        Path(SubstructureOutputDir).mkdir(exist_ok=True)

        for CTSegFile in CTSegFiles:
            NewCTSegFile = os.path.join(SubstructureOutputDir,os.path.basename(CTSegFile))
            VolReg.TransformVolume(NonRigidTFormMask, NewCTSegFile, CTSegFile)

    else:
        if SegmentationMethod == 'Direct':
            SegImageFile = CBCTNiftiFile
        elif SegmentationMethod == 'Synthetic':
            SegImageFile = os.path.join(TempDir, 'CTToCBCT.mha')
            #SegImageFile = os.path.join(OutputDir, 'SyntheticCT.mha')
            #VolReg.TransformVolume(NonRigidTForm, OutputFile=SegImageFile, FixedVolume=PlanningCTNiftiFile)
            #assert Path(SegImageFile).exists(), 'Error creating Synthetic CT image'

        #Run the platipy segmentation method
        SubstructureOutputDir = os.path.join(OutputDir, 'OutputSegmentations_Nifti')
        Path(SubstructureOutputDir).mkdir(exist_ok=True)
        GenerateCardiacStructures(SegImageFile, OutputDir=SubstructureOutputDir)

    """
    Convert the segmentations to Dicom
    """
    if os.path.isdir(CBCTDir):
        print('Converting segmentations to Dicom Format')
    
        DcmOutputDir = os.path.join(OutputDir, 'OutputSegmentations_Dicom')
        Path(DcmOutputDir).mkdir(exist_ok=True)
        WriteDicomStructs(SubstructureOutputDir, CBCTDir, DcmOutputDir)

    # Delete temporary dicom files
    if not KeepTempFiles:
        shutil.rmtree(TempDir)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Function for segmenting cardiac structures on CBCT images/volumes.')
    parser.add_argument('--CBCTDir',required=True,type=str, help='Location of the Cone-beam CT that is to be segmented. Can be a Dicom Series or Volume file.')
    parser.add_argument('--OutputDir',default='./CBCTSegmentations',type=str,help='Directory where the created segmentations will be created. Default is ./CBCTSegmentations')
    parser.add_argument('--SegmentationMethod',default='Synthetic',type=str,help='The method used to segment the CBCT image {Synthetic|Transform|Direct}. Default is Synthetic')
    parser.add_argument('--PlanningCTDir',type=str, default='',help='Location of the Planning CT that is to be segmented. Can be a Dicom Series or Volume file. Default is None')
    parser.add_argument('--ElastixParamDir',type=str,default='',help='Location of the elastix parameter files used for the registrations. Default is the parameters is the provided ElastixParameterFiles')
    parser.add_argument('--ElastixRunDir',type=str,default='',help='Location of the bin and lib directories from the installed/downaloded version of elastix to be used. Needed for linux implementations')
    parser.add_argument('--StructFile',type=str,default='',help='Location of the structures contoured from the planning CT File. Default is None')
    parser.add_argument('--KeepTempFiles',action='store_true',help='If true the temporary files and directories created will not be deleted. If False these files will be deleted.')
    
    args = parser.parse_args()
    
    assert Path(args.CBCTDir).exists(), "CBCT Directory {} does not exist".format(args.CBCTDir)
    
    CreateCBCTSegmentations(args.CBCTDir,
                            args.OutputDir,
                            SementationMethod=args.SegmentationMethod,
                            PlanningCTDir=args.PlanningCTDir,
                            ElastixParamDir=args.ElastixParamDir,
                            StructFile=args.StructFile,
                            KeepTempFiles=args.KeepTempFiles)
