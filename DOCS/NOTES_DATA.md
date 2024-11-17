**RF_FULGUR**

**Fichiers et Orientations**
- left  = left
- right = right
- ----  = right

**Fichiers Problématiques**
Doublons
- FULGUR_028_61082_label_4.nii
- FULGUR_029_61082_label_4.nii
- FULGUR_059_236946_label_4.nii
- FULGUR_076_46061_label_4.nii

Erreurs
- FULGUR_029_15058_right_label_4.nii

```shell
Loading: ./CODE/DATA/RF_FULGUR\FULGUR_029_15058_right_label_4.nii.gz
Traceback (most recent call last):
  File "c:\Users\sacha\Desktop\PROJ_REDEV\SOURCE\CODE\ssm_full.py", line 203, in <module>
    Run_Pipeline(args)
  File "c:\Users\sacha\Desktop\PROJ_REDEV\SOURCE\CODE\ssm_full.py", line 55, in Run_Pipeline
    shape_seg = sw.Image(shape_filename)
RuntimeError: C:\bdeps\ITK\Modules\IO\NIFTI\src\itkNiftiImageIO.cxx:1980:
ITK ERROR: ITK only supports orthonormal direction cosines.  No orthonormal definition found!
(shapeworks) PS C:\Users\sacha\Desktop\PROJ_REDEV\SOURCE> 
```