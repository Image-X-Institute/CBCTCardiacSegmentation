"""
Functions to make calling and using the caridac segmentation tool a bit easier. 
Might delete if there are not enough to justify a seperate file.
Large Amounts of this code are stolen from platipy[cardiac] module
"""

import glob
import numpy as np
import SimpleITK as sitk
from pathlib import Path
from shutil import copy2, rmtree
from os.path import join, split, splitext

# Import platipy modules

from platipy.dicom.io.crawl import process_dicom_directory

from platipy.imaging.projects.cardiac.run import (
    run_hybrid_segmentation
)

def ConvertFileType(InputFile, OutputFile, NewAxes = [0, 1, 2], NewOffsetFlag=False,MaskFlag=False,
                    ResampleFlag=False,ReferenceImage=sitk.Image()):
    """
    Use to convert between nifti and mha file types or vice versa.
    :param InputFile: file name to input file. Input type is any SimpleITK input types for ReadImage.
    :param OutputFile: desired file name. Has to be a file type that is SimpleITK.
    :param NewAxes: Order of the axes in OutputFile. Default is [0, 1, 2]
    :param NewOffsetFlag: if True the offset value for the Output image will be recalculated. If False offset values
    will be the same as the input image.
    :param MaskFlag: If true then the voxel values won't be rescaled
    :return:
    """
    Img = sitk.ReadImage(InputFile)
    if NewOffsetFlag:
        #Centre image
        OriginNew = tuple(-0.5*np.array(Img.GetSize())*np.array(Img.GetSpacing()))
        Img.SetOrigin(OriginNew)
    if (NewAxes[0] == 0) and (NewAxes[1] == 1) and NewAxes[2] == 2:
        # Don't rotate the image
        sitk.WriteImage(Img, OutputFile)
    else:
        Spacing = Img.GetSpacing()
        Origin = Img.GetOrigin()


        Arr = sitk.GetArrayFromImage(Img)
        Arr2 = np.transpose(Arr, [2, 1, 0])
        Arr3 = np.transpose(Arr2, NewAxes)
        Arr4 = np.transpose(Arr3[:, ::-1, ::-1], [2, 1, 0])
        #Img2 = sitk.PermuteAxes(Img, order=NewAxes)
        #Img2.SetDirection(Img.GetDirection())

        if not MaskFlag:
            Img2 = sitk.GetImageFromArray((Arr4*1000)/0.013 - 1000)
        else:
            Img2 = sitk.GetImageFromArray(Arr4)
        Img2.SetSpacing([Spacing[NewAxes[0]], Spacing[NewAxes[1]], Spacing[NewAxes[2]]])
        Img2.SetOrigin([Origin[NewAxes[0]], Origin[NewAxes[1]], Origin[NewAxes[2]]])
        if ResampleFlag:
            if MaskFlag:
                interpType = sitk.sitkNearestNeighbor
                defaultValue = 0
            else:
                interpType = sitk.sitkBSpline3
                defaultValue=-1000
            Img2 = sitk.Resample(Img2,size=Img2.GetSize(), outputSpacing=ReferenceImage.GetSpacing(), outputPixelType=Img2.GetPixelID(),
                                 interpolator=interpType, defaultPixelValue=defaultValue)
        if not MaskFlag:
            sitk.WriteImage(sitk.Cast(Img2, sitk.sitkInt16), OutputFile)
        else:
            sitk.WriteImage(sitk.Cast(Img2, sitk.sitkUInt8), OutputFile)

def DoDicomProcessing(CTDicomDir, OutputDir='./DicomProcessing', StructFile='', DoseDir='', ProcessFile=True,
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

def CentreImage(ImgFile):
    """
    Alter the Offset/Origin parameter files of the image so the centre pixel is at (0,0,0)

    Parameters
    ----------
    ImgFile : str
        The name of the file to be centred.

    Returns
    -------
    CTImgOrigin : tuple
        The unedited origin of ImgFile.
    CTNewOrigin : tuple
        The new origin of ImgFile.

    """
    CTImg = sitk.ReadImage(ImgFile)

    CTImgOrigin = CTImg.GetOrigin()

    CTNewOrigin = -0.5 * (np.array(CTImg.GetSize()) * np.array(CTImg.GetSpacing()))

    CTImg.SetOrigin(CTNewOrigin)

    sitk.WriteImage(CTImg, ImgFile)

    return CTImgOrigin, CTNewOrigin

def PadBinaryVol(VolFileName, OutputFileName='', PadWidth=5):
    """
    Increase mask volume of VolFileName by padding equally around the volume

    Parameters
    ----------
    VolFileName : str
        The name of the volume to be padded.
    OutputFileName : str, optional
        The filename of the output padded file. If empty the original file will be overwritten.
        The default is ''.
    PadWidth : int, optional
        The width of the padding (Padding Kernal = [PadWidth,PadWidth,PadWidth]). The default is 5.

    Returns
    -------
    None.

    """
    
    if not OutputFileName:
        OutputFileName = VolFileName

    Vol = sitk.ReadImage(VolFileName)

    BinVol = sitk.BinaryDilate(image1=sitk.Cast(Vol,sitk.sitkUInt8), kernelRadius=[PadWidth,PadWidth,PadWidth])

    sitk.WriteImage(BinVol, OutputFileName)

def GenerateCardiacStructures(ImagePath, OutputDir="/Substructures"):
    """
    Helper function for generating cardiac substructures from a nifti file.
    :param ImagePath: string, name of the file to be segmented.
    :param OutputDir: str, name of the directory where the segmentations will be written to. default: "/Substructures".
    :return: error_code: bool, -1 if something failed, otherwise 0.
    :return: StructureFileNames: list, List of the name of the files for each structure created.
    """
    StructureFileNames = []

    # Check if image exists
    if not Path(ImagePath).exists():
        print("Image File {} does not exist".format(ImagePath))
        return -1, StructureFileNames

    # Read Image
    Img = sitk.ReadImage(ImagePath)

    # Compute the auto-segmented sub-structures
    auto_structures, _ = run_hybrid_segmentation(Img)

    StructureFileNames = WriteCardiacSegmentations(auto_structures, OutputDir)

    """

    StructureFileNames = list(auto_structures.keys())

    # Save the results
    Path(OutputDir).mkdir(exist_ok=True, parents=True)

    for struct_name in list(auto_structures.keys()):
        sitk.WriteImage(auto_structures[struct_name], str(Path(OutputDir).joinpath(f"{struct_name}.nii.gz")))

    print(f"Segmentations saved to: {OutputDir}")
    """
    return 0, StructureFileNames

def WriteCardiacSegmentations(auto_structures,OutputDir):
    """
    Write the cardiac segmentations auto_structures to directory OutputDir

    Parameters
    ----------
    auto_structures : dict
        dictionary of the cardiac structures, where each element is a SimpleITK image.
    OutputDir : str
        Name of the directory where the segmentations will be written to.

    Returns
    -------
    StructureFileNames : list
        List containing the names of structures that were written

    """
    StructureFileNames = list(auto_structures.keys())

    # Save the results
    Path(OutputDir).mkdir(exist_ok=True, parents=True)

    for struct_name in list(auto_structures.keys()):
        sitk.WriteImage(auto_structures[struct_name], str(Path(OutputDir).joinpath(f"{struct_name}.nii.gz")))

    print(f"Segmentations saved to: {OutputDir}")

    return StructureFileNames
