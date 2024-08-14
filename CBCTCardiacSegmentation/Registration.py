"""
Functions for helping with using elastix and transformix for registration and transformation stuff
"""

import os
import shutil
import platform
import numpy as np
import SimpleITK as sitk
from pathlib import Path
from subprocess import run


class VolumeRegistration:

    def __init__(self, RegOutputDir='', ParamDir='', RigidParamFile='', NonRigidParamFile='', InverseParamFile='',
                 RigidNonRigidParamFile='',TranslationParamFile='',ElastixDir='',GPUEnabled=False):

        if not ParamDir:
            #If no elastix parameter directory defined then get the one
            mod_path = Path(__file__).parent
            relative_path_2 = '../ElastixParameterFiles'
            ParamDir = (mod_path / relative_path_2).resolve()
        
        assert Path(ParamDir).exists(), 'Elastix parameter directory {} does not exist'.format(ParamDir)

        self.RegOutputDir = RegOutputDir

        if platform.system() == 'Linux':
            assert not(not ElastixDir),'Directory to elastix bin/lib files needs to be added for linux'

        self.ElastixDir = ElastixDir

        if not ParamDir:
            self.RigidParamFile = RigidParamFile
            self.NonRigidParamFile = NonRigidParamFile
            self.InverseParamFile = InverseParamFile
            self.RigidNonRigidParamFile = RigidNonRigidParamFile
            self.TranslationParamFile = TranslationParamFile

        else:
            if GPUEnabled:
                self.RigidParamFile = os.path.join(ParamDir, 'Elastix_Rigid_OpenCL.txt')
                self.NonRigidParamFile = os.path.join(ParamDir, 'Elastix_BSpline_OpenCL.txt')
                self.InverseParamFile = os.path.join(ParamDir, 'Elastix_BSpline_Inverse.txt')
                self.RigidNonRigidParamFile = os.path.join(ParamDir, 'Elastix_Rigid_OpenCL_RigidPenalty.txt')
            else:
                self.RigidParamFile = os.path.join(ParamDir, 'Elastix_Rigid.txt')
                self.NonRigidParamFile = os.path.join(ParamDir, 'Elastix_BSpline.txt')
                self.InverseParamFile = os.path.join(ParamDir, 'Elastix_BSpline_Inverse.txt')

            self.TranslationParamFile = os.path.join(ParamDir, 'Elastix_Translation.txt')

    def DoDeformation(self,FixedVolume,MovingVolume,OutputFile,paramFile,
                         FixedMask='',MovingMask='',InitTransform='',DeleteVolumeFlag=True):
        """
        Sets up the files for the elastix registration, called using the command line.
        For compatible files see https://github.com/SuperElastix/elastix/wiki
        Parameters
        ----------
        FixedVolume : str
            The file name for the fixed volume for the registration.
        MovingVolume : str
            The file name for the fixed volume for the registration.
        OutputFile : str
            The file name for the output parameter file from the registration.
        paramFile : str
            The file name for the input parameter file that contains the registration information.
        FixedMask : str, optional
            The file name for the fixed volume mask. The default is ''.
        MovingMask : str, optional
            The file name for the moving volume mask. The default is ''.
        InitTransform : str, optional
            The file name for the initial transformation file. The default is ''.
        DeleteVolumeFlag : bool, optional
            If true, after the registration the output volume is deleted. If False
            the output volume is renamed to the same name as OutputFile (but with a
            .mha file extension). The default is True.

        Returns
        -------
        int
            if -1: Registration failed.
            if 0: Registration Successful.

        """

        OutputDir = self.RegOutputDir
        #OutputDir = os.path.dirname(OutputFile)

        #OutputDir = "~/"

        # Define string for registration
        CmdStr = ('elastix -f "' + FixedVolume + '" -m "' + MovingVolume + '" -out "' + OutputDir + '" -p "'
                  + paramFile + '" -fMask "' + FixedMask + '" -mMask "' + MovingMask + '" -t0 "'
                  + InitTransform + '"')

        # Run command from terminal
        self.CallFunctionFromCmdLine(CmdStr)

        OutputParamFile = os.path.join(OutputDir, "TransformParameters.0.txt")

        # Check if the registration was successful by looking for output files
        if not Path(OutputParamFile).exists():
            print('Error with the registration')
            return -1
        else:
            #os.rename(OutputParamFile, OutputFile)
            shutil.copy2(OutputParamFile, OutputFile)
            os.remove(OutputParamFile)
            if Path(os.path.join(OutputDir, "result.0.mha")).exists():
                if DeleteVolumeFlag:
                    #os.remove(os.path.join(OutputDir, "result.0.mha"))
                    pass
                else:
                    name = os.path.basename(OutputFile)
                    shutil.copy2(os.path.join(OutputDir, "result.0.mha"),
                                 os.path.join(os.path.dirname(OutputFile), os.path.splitext(name)[0] + '.mha'))
                    #os.rename(os.path.join(OutputDir, "result.0.mha"),
                    #          os.path.join(OutputDir, os.path.splitext(name)[0] + '.mha'))
                os.remove(os.path.join(OutputDir, "result.0.mha"))
            return 0

    def TransformVolume(self, ParamFile, OutputFile, FixedVolume):
        """
        Deform a volume (FixedVolume) using a parameter file

        Parameters
        ----------
        ParamFile : str
            The parameter file to be transformed.
        OutputFile : str
            The file name of the deformed volume.
        FixedVolume : str
            The file name of the volume that is to be deformed
        Returns
        -------
        int
            if -1: Transformation failed.
            if 0: Transformation Successful.

        """
        #OutputDir = os.path.dirname(OutputFile)
        OutputDir = self.RegOutputDir

        #os.system('transformix -in "' + FixedVolume + '" -tp "' + ParamFile + '" '
        #          + '-out "' + OutputDir + '"')
        CmdStr = 'transformix -in "' + FixedVolume + '" -tp "' + ParamFile + '" ' + '-out "' + OutputDir + '"'
        self.CallFunctionFromCmdLine(CmdStr)

        TFormOutputFile = os.path.join(OutputDir, "result.mha")

        if Path(TFormOutputFile).exists():
            sitk.WriteImage(sitk.ReadImage(TFormOutputFile), OutputFile)
            os.remove(TFormOutputFile)
            return 0
        else:
            print('Transformation Failed')
            return -1


    def CallFunctionFromCmdLine(self,CmdStr):
        # Run command from terminal
        if platform.system() == 'Linux':
            run(CmdStr, shell=True, env={"PATH": os.path.join(self.ElastixDir,'bin'), "LD_LIBRARY_PATH": os.path.join(self.ElastixDir,'lib')})
        else:
            run(CmdStr)

    def Translation(self, FixedVolume, MovingVolume, OutputFile,
                         FixedMask='', MovingMask='', InitTransform='',
                        DeleteVolumeFlag=True):
        """
        Shortcut function for doing translation only component of rigid registration. Calls the DoDeformation function

        Parameters
        ----------
        FixedVolume : str
            The file name for the fixed volume for the registration.
        MovingVolume : str
            The file name for the fixed volume for the registration.
        OutputFile : str
            The file name for the output parameter file from the registration.
         FixedMask : str, optional
             The file name for the fixed volume mask. The default is ''.
         MovingMask : str, optional
             The file name for the moving volume mask. The default is ''.
         DeleteVolumeFlag : bool, optional
             If true, after the registration the output volume is deleted. If False
             the output volume is renamed to the same name as OutputFile (but with a
             .mha file extension). The default is True.

        Returns
        -------
        int
            if -1: Registration failed.
            if 0: Registration Successful.

        """
        return self.DoDeformation(FixedVolume, MovingVolume, OutputFile, self.TranslationParamFile,
                                  FixedMask=FixedMask, MovingMask=MovingMask, InitTransform=InitTransform,
                                  DeleteVolumeFlag=DeleteVolumeFlag)
    def RigidDeformation(self, FixedVolume, MovingVolume, OutputFile,
                         FixedMask='', MovingMask='', InitTransform='', DeleteVolumeFlag=True):
        """
        Shortcut function for doing rigid registration. Calls the DoDeformation function

        Parameters
        ----------
        FixedVolume : str
            The file name for the fixed volume for the registration.
        MovingVolume : str
            The file name for the fixed volume for the registration.
        OutputFile : str
            The file name for the output parameter file from the registration.
         FixedMask : str, optional
             The file name for the fixed volume mask. The default is ''.
         MovingMask : str, optional
             The file name for the moving volume mask. The default is ''.
         InitTransform : str, optional
             The file name for any initial transformation parameters. The default is ''.
         DeleteVolumeFlag : bool, optional
             If true, after the registration the output volume is deleted. If False
             the output volume is renamed to the same name as OutputFile (but with a
             .mha file extension). The default is True.

        Returns
        -------
        int
            if -1: Registration failed.
            if 0: Registration Successful.

        """
        return self.DoDeformation(FixedVolume, MovingVolume, OutputFile, self.RigidParamFile,
                                  FixedMask=FixedMask, MovingMask=MovingMask,InitTransform=InitTransform,
                                  DeleteVolumeFlag=DeleteVolumeFlag)


    def NonRigidDeformation(self, FixedVolume, MovingVolume, OutputFile,
                            FixedMask='', MovingMask='', InitTransform='', DeleteVolumeFlag=True):
        """
        Shortcut function for doing nonrigid registration. Calls the DoDeformation function

        Parameters
        ----------
        FixedVolume : str
            The file name for the fixed volume for the registration.
        MovingVolume : str
            The file name for the fixed volume for the registration.
        OutputFile : str
            The file name for the output parameter file from the registration.
         FixedMask : str, optional
             The file name for the fixed volume mask. The default is ''.
         MovingMask : str, optional
             The file name for the moving volume mask. The default is ''.
         InitTransform : str, optional
             The file name for any initial transformation parameters. The default is ''.
         DeleteVolumeFlag : bool, optional
             If true, after the registration the output volume is deleted. If False
             the output volume is renamed to the same name as OutputFile (but with a
             .mha file extension). The default is True.

        Returns
        -------
        int
            if -1: Registration failed.
            if 0: Registration Successful.

        """
        return self.DoDeformation(FixedVolume, MovingVolume, OutputFile, self.NonRigidParamFile,
                                  FixedMask=FixedMask, MovingMask=MovingMask,
                                  InitTransform=InitTransform, DeleteVolumeFlag=DeleteVolumeFlag)


    def ReadTFormValues(self,ParamFile):
        """
        Read the transformation parameters from either the rigid or non-rigid
        parameter file

        Parameters
        ----------
        ParamFile : str
            FileName of the parameter that is to be read.

        Returns
        -------
        Params : numpy array
            Array of transformation parameters where each index of the array is
            a new parameter.

        """
        Params = []
        with open(ParamFile) as f:
            for line in f:
                if '(TransformParameters' in line:
                    Params = np.fromstring(line[len('(TransformParameters'):],sep=" ")
                    break
        return Params


    def EditTFormFile(self,ParamFileInit,ParamFileNew='',InitTFormFile='',ReverseParamFlag=False):
        """
        Edit elastix registration parameter files to transform masks instead of images         

        Parameters
        ----------
        ParamFileInit : str
            Filename of the parameter file to be edited. Usually an output parameter file from elasix
        ParamFileNew : str, optional
            If given then the edited files will be rewritten to a new parameter file. If empty
            then the old parameter file will be overwritten. The default is ''.
        InitTFormFile : str, optional
            Add an optional initial parameter file. The default is ''.
        ReverseParamFlag : str, optional
            If True the magnitude of the transformation parameters are reversed. The default is False.

        Returns
        -------
        None.

        """
        if not ParamFileNew:
            ParamFileNew = ParamFileInit

        linesNew = []

        with open(ParamFileInit) as f:
            for line in f:
                if 'FinalBSplineInterpolationOrder 3' in line:
                    linesNew.append('(FinalBSplineInterpolationOrder 0)\n')
                elif 'DefaultPixelValue' in line:
                    linesNew.append('(DefaultPixelValue 0)\n')
                elif 'InitialTransformParametersFileName' in line:
                    if not InitTFormFile:
                        linesNew.append(line)
                    else:
                        linesNew.append('(InitialTransformParametersFileName "{}")\n'.format(InitTFormFile))
                elif '(TransformParameters' in line:
                    if ReverseParamFlag:
                        StrSplit = str.split(line[1:-2], ' ')
                        StrNew = '(' + StrSplit[0]
                        for i in range(1, len(StrSplit)):
                            Num = float(StrSplit[i])
                            StrNew = StrNew + ' ' + str(-Num)
                        StrNew = StrNew + ')\n'
                        linesNew.append(StrNew)
                    else:
                        linesNew.append(line)
                else:
                    linesNew.append(line)

        with open(ParamFileNew, 'w') as f:
            f.writelines(linesNew)
