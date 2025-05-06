# -*- coding: utf-8 -*-
"""
Created on Tue May  6 13:25:54 2025

@author: mgar5380
"""

import SimpleITK as sitk
from platipy.imaging.tests.data import get_lung_nifti
from platipy.imaging.projects.cardiac.run import run_hybrid_segmentation

def TestSegmentation():

    # Download the test data
    data_path = get_lung_nifti()

    # Pick out a case to run on
    test_pat_path = data_path.joinpath("LCTSC-Test-S1-201")
    test_image = sitk.ReadImage(str(test_pat_path.joinpath("IMAGES/LCTSC_TEST_S1_201_0_CT_0.nii.gz")))

    # Compute the auto-segmented sub-structures
    auto_structures, _ = run_hybrid_segmentation(test_image)

    # Save the results
    output_directory = test_pat_path.joinpath("substructures")
    output_directory.mkdir(exist_ok=True)

    for struct_name in list(auto_structures.keys()):
        sitk.WriteImage(auto_structures[struct_name], str(output_directory.joinpath(f"{struct_name}.nii.gz")))

    print(f"Segmentations saved to: {output_directory}")
    
    
TestSegmentation()