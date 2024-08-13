# -*- coding: utf-8 -*-
"""
Created on Tue Jul 30 14:57:00 2024

@author: mgar5380
"""
import re
import glob
from os import listdir
from pathlib import Path
from pydicom import dcmread
from shutil import copy2, rmtree
from os.path import join, split, splitext, isdir, isfile

from platipy.dicom.io.crawl import process_dicom_directory
from platipy.dicom.io.nifti_to_rtstruct import convert_nifti

def WriteDicomStructs(NiftiMaskDir, CTDcmDir, OutputDir, CTPat='CT*dcm'):
    """
    Convert generated segmentations (nifti) to Dicom files

    Parameters
    ----------
    NiftiMaskDir : str
        Name of the directory where the nifti structures are stored  
    CTDcmDir : str
        Name of the directory where reference dicom data is stored
    OutputDir : str
        Name of the directory to where the output dicom file will be written.
    CTPat : str, optional
        Pattern used to match the reference dicom data. The default is 'CT*dcm'.

    Returns
    -------
    None.

    """

    #dictionary containing path of nifti files
    masks = {}
    for m in listdir(Path(NiftiMaskDir)):
        name = m.split('.')[0]
        mask_path = join(NiftiMaskDir, m)   #str(output_dir_STRUCT / m)
        masks[name] = mask_path

    DcmFile = glob.glob(join(CTDcmDir, CTPat))

    convert_nifti(
        dcm_path=DcmFile[0],
        mask_input=masks,
        output_file=join(OutputDir, "struct.dcm")
    )

def PrepareCTData(CTDir,OutputDir='',StructFile='',PreviousNiftiFiles=[],KeepTempFiles=False):
    """
    Convert the CT and CBCT data from a dicom format to a nifti format, and return the nifti file
    as well as any structures that are included in the input dicom files.     

    Parameters
    ----------
    CTDir : str
        Either the path to the directory of CT/CBCT Dicom files, or a path to a CT/CBCT volume.
    OutputDir : str, optional
        Name of the directory where the Output Nifti files will be written to. The default is ''.
    StructFile : str, optional
        Name of the DICOM structure file to be included in the dicom->Nifti conversion. If StructFile=='' then
        it is assumed that there is no corresponding Structure file. The default is ''.
    PreviousNiftiFiles : {str,list}, optional
        Any previous nifti files that have been created, that are in the same directory as the files to be created
        The default is [].
    KeepTempFiles : bool, optional
        If True the temporary dicom files are not deleted after the dicom to nifti conversion. The default is False.

    Returns
    -------
    CTNiftiFile : str
        The filename of the nifti file corresponding to the data in CTDir
    StructNiftiDir : str
        The filename of the STRUCTURE nifti file corresponding to the data in StructFile

    """
    if isdir(CTDir):    
        if isdir(StructFile):
            StructFileDCM = StructFile
        else:
            StructFileDCM = ''
            StructNiftiDir = ''
    
        CTPat = 'CT*.dcm'
        DcmFiles = glob.glob(join(CTDir,CTPat))
        
        if not DcmFiles:
            CTPat = '*.dcm'
            DcmFiles = glob.glob(join(CTDir,CTPat))    
            assert not(not DcmFiles),'No dicom files detected in directory {}'.format(CTDir)
                
        DcmInfo = dcmread(DcmFiles[0])
    
        del DcmFiles
    
        DoDicomProcessing(CTDir, OutputDir=OutputDir, 
                          StructFile=StructFileDCM,
                          RemoveDicomFiles=not(KeepTempFiles),
                          CTPat=CTPat)    
    
        # Get the data in the parent sorting field, clean with RegEx
        PatientIDCT = re.sub(
            r"[^\w]", "_", str(DcmInfo["PatientName"].value)
        ).upper()
    
        #PatientIDCT = DcmInfo.PatientID.replace('^','_').replace(" ",'_')
        
        NiftiFiles = glob.glob(join(OutputDir,'Nifti',PatientIDCT,'IMAGES','*.nii.gz'))
        
        CTNiftiFile = NiftiFiles[0]
        count = 0
        while CTNiftiFile in PreviousNiftiFiles:
            count = count + 1
            CTNiftiFile = NiftiFiles[count]
            
        if StructFileDCM:
            StructNiftiDir = join(OutputDir,'Nifti',PatientIDCT,'STRUCTURES')
            
    elif isfile(CTDir):
        CTNiftiFile = CTDir
        StructNiftiDir = ''

    return CTNiftiFile,StructNiftiDir

def DoDicomProcessing(CTDicomDir, OutputDir='/DicomProcessing', StructFile='', DoseDir='', ProcessFile=True,
                      RemoveDicomFiles=False,CTPat='*'):
    """
    Organise the dicom files into the one folder, and then convert from dicom files to nifti files.
    :param CTDicomDir: str, directory where the ct dicom files are stored.
    :param OutputDir: str, directory where the temporary dicom and nifti files will be written to.
    :param StructFile: str, rtstruct dicom file to process with the CT dicom files.
    If empty no nifti struct file is created. Default is ''.
    :param DoseDir: str, directory where the dicom dose file(s) for processing are stored.
    If empty no nifti dose file(s) are created.  Default is ''.
    :param ProcessFile: bool, If True the dicom files will be converted to nifti files. Default is True.
    :param RemoveDicomFiles: bool, If True after converting the dicom files to nifti files, the dicom files
    in OutputDir (and NOT the original dicom files) will be deleted. Default is False
    :return: None
    """
    Path(OutputDir).mkdir(exist_ok=True, parents=True)

    # Output directory for Temp DicomFiles
    DicomOutput = join(OutputDir, 'Dicom')
    Path(DicomOutput).mkdir(exist_ok=True)

    # Output directory for output nifti files
    NiftiOutput = join(OutputDir, 'Nifti')
    Path(NiftiOutput).mkdir(exist_ok=True)

    # Copy CT Dicom files across
    CTDicomOutput = join(DicomOutput, 'ct')
    Path(CTDicomOutput).mkdir(exist_ok=True)

    # Get list of dicom files to copy over
    CTDicomList = glob.glob(join(CTDicomDir, CTPat))

    for dcmfile in CTDicomList:
        LoopFileName, LoopFileExt = splitext(dcmfile)
        if LoopFileExt == '.dcm':
            name = split(dcmfile)[-1]
        else:
            name = split(dcmfile + '.dcm')[-1]
        copy2(dcmfile, join(CTDicomOutput, name))

    if StructFile:
        # Copy Struct file across
        StructDicomOutput = join(DicomOutput, 'rtstruct')
        Path(StructDicomOutput).mkdir(exist_ok=True)

        LoopFileName, LoopFileExt = splitext(StructFile)
        if LoopFileExt == '.dcm':
            name = split(StructFile)[-1]
        else:
            name = split(StructFile + '.dcm')[-1]
        copy2(StructFile, join(StructDicomOutput, name))

    if DoseDir:
        # Copy dose file(s) across
        DoseDicomOutput = join(DicomOutput, 'dose')
        Path(DoseDicomOutput).mkdir(exist_ok=True)

        # Get list of dose files
        doseList = glob.glob(join(DoseDir, '*'))

        for doseFile in doseList:
            LoopFileName, LoopFileExt = splitext(doseFile)
            if LoopFileExt == '.dcm':
                name = split(doseFile)[-1]
            else:
                name = split(doseFile + '.dcm')[-1]
            copy2(doseFile, join(DoseDicomOutput, name))

    if ProcessFile:
        # Convert organised dicom files to nifti files
        process_dicom_directory(DicomOutput, output_directory=Path(NiftiOutput))

        # Delete temporary dicom files
        if RemoveDicomFiles:
            rmtree(DicomOutput)