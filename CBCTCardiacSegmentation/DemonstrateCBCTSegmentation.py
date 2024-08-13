# -*- coding: utf-8 -*-
"""
Created on Fri Aug  9 15:18:35 2024

@author: mgar5380
"""

#Sample Data can be downloaded from the cancer imaging archive. For this example we will be using data from the 4d-lung dataset. (https://www.cancerimagingarchive.net/collection/4d-lung/)

#Download example data
#Download the dicom data for one phase of the 4D-CBCT scan, and one phase of the 4D-CT. For example for patientID 100_HM10395, download the <P4^P100^S100^I0, Gated, 0.0%> CBCT dicom data from the Sep 14, 1997, and the <P4^P100^S300^I00003, Gated, 0.0%A> CT dicom data from the Jul 01, 2003.

from CreateCBCTSegmentations import CreateCBCTSegmentations
 
#DownloadDirectory = 'Z://2RESEARCH/6_Temp/MarkLungData/manifest-1723179013471/' #Directory where the data is downloaded to
DownloadDirectory = 'E://RAVENTA/Mannheim/'

#Define input data sources
#CBCTDicomDir = DownloadDirectory + "4D-Lung/100_HM10395/09-15-1997-NA-p4-69351/500.000000-P4P100S100I0 Gated 0.0-90726"
#CTDicomDir = DownloadDirectory + "4D-Lung/100_HM10395/07-02-2003-NA-p4-14571/1.000000-P4P100S300I00003 Gated 0.0A-29193"
CBCTDicomDir = DownloadDirectory + "Patient CBCT images/PAT01/Fx1"
CTDicomDir = DownloadDirectory + "Patient CT images/PAT01"

#Define directory where the data will be written to
#OutputDir = DownloadDirectory + "4D-Lung/100_HM10395/CardiacSegmentations"
OutputDir = DownloadDirectory + "CBCTSegmentations2"

#Create the segmentations
CreateCBCTSegmentations(CBCTDicomDir,OutputDir=OutputDir,PlanningCTDir=CTDicomDir)