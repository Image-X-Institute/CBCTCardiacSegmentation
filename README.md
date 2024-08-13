# CBCTCardiacSegmentation

**Author:** *Mark Gardner*

This code will generate cardiac segmentations in CBCT images. The input is dicom or volume files of a CBCT image and an optional planning CT and will output dicom and nifti segmentations of cardiac segmentations that are compatible with the input CBCT image. **Currently this works in Linux only**


## Setup/Build/Install

The module will soon be able to be installed using pip:

```
pip install CBCTCardiacSegmentation
```

This code uses the platipy repo (https://github.com/pyplati/platipy). If the platipy module is not automatically installed when installing the CTHeadDeformation code, the platipy library can be installed separately using the installation instructions (https://pyplati.github.io/platipy/getting_started.html). 

Install elastix (https://elastix.lumc.nl/index.php)

## Usage

Sample Data can be downloaded from the cancer imaging archive. For this example we will be using data from the 4d-lung dataset.  (https://www.cancerimagingarchive.net/collection/4d-lung/)

### Download example data

Download the dicom data for one phase of the 4D-CBCT scan, and one phase of the 4D-CT. For example for patientID 100_HM10395, download the <P4^P100^S100^I0, Gated, 0.0%> CBCT dicom data from the Sep 14, 1997, and the <P4^P100^S300^I00003, Gated, 0.0%A> CT dicom data from the Jul 01, 2003.

The CBCT and CT directories can then be set to:

```
CBCTDicomDir = "<Directory where data was downloaded to>/4D-Lung/100_HM10395/09-15-1997-NA-p4-69351/500.000000-P4P100S100I0 Gated 0.0-90726"
CTDicomDir = "<Directory where data was downloaded to>/4D-Lung/100_HM10395/07-02-2003-NA-p4-14571/1.000000-P4P100S300I00003 Gated 0.0A-29193"
```
The directory where the created segmentations can also be set
```
OutputDir = "<Directory where data was downloaded to>/4D-Lung/100_HM10395/CardiacSegmentations
```

### Run in python script
See [DemonstrateCBCTSegmentation.py](https://github.com/Image-X-Institute/CBCTCardiacSegmentation/blob/master/CBCTCardiacSegmentation/DemonstrateCBCTSegmentation.py) for an example python script. 
```
from  CBCTCardiacSegmentation import CreateCBCTSegmentations
CreateCBCTSegmentations(CBCTDicomDir,OutputDir=OutputDir,PlanningCTDir=CTDicomDir)
```

### Run in a command line

In a command line (such as anaconda command prompt) navigate to the directory that the CTHeadDeformation repo was cloned to and run 
```python CreateCBCTSegmentations.py <CBCTDicomDir> --OutputDir <OutputDir> --PlanningCTDir <CTDicomDir>``` 

### Function Options
 A summary of the input options are shown below
 ```
  --CBCTDir CBCTDIR     Location of the Cone-beam CT that is to be segmented. Can be a Dicom Series or Volume file.
  --OutputDir OUTPUTDIR
                        Directory where the created segmentations will be created. Default is ./CBCTSegmentations. (Optional)
  --SegmentationMethod SEGMENTATIONMETHOD
                        The method used to segment the CBCT image {Synthetic|Transform|Direct}. Default is Synthetic. (Optional)
  --PlanningCTDir PLANNINGCTDIR
                        Location of the Planning CT that is to be segmented. Can be a Dicom Series or Volume file.
                        Default is None. (Optional)
  --ElastixParamDir ELASTIXPARAMDIR
                        Location of the elastix parameter files used for the registrations. Default is the parameters
                        is the provided ElastixParameterFiles. (Optional)
  --StructFile STRUCTFILE
                        Location of the structures contoured from the planning CT File. Default is None
  --KeepTempFiles       If true the temporary files and directories created will not be deleted. If False these files
                        will be deleted. (Optional)
 ```
 
 The different segmentation methods are:
 -Synthetic: A synthetic CT is created by deforming a planning CT to match the CBCT. CT cardiac segmentation is then applied to this image. 
 -Transform: The Planning CT is first segmented. The planning CT and CBCT are deformably registered and the output transformation is used to map the planning CT segmentations to the CBCT.
 -Direct: The CT segmentation method is directly applied to the CBCT image. May perform unreliably, particularly for noisy CBCT images. 
 
 
## Directory Structure
CBCTCardiacSegmentation - Main code directory.
ElastixParameterFiles - Contains parameter files required for elastix.
docs - Files and info for the wiki. 
examples - Files and data for examples of how to run the code.
tests - Files for testing the code. 
