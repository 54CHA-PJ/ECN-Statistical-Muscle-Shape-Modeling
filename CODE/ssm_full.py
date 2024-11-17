import os
import glob
import subprocess
import shapeworks as sw
from pathlib import Path
import numpy as np
import time
from tqdm import tqdm

def Run_Pipeline(args):
    
    start_time = time.time()    
    
    # -----------------------------------------------------------------------
    # Step 1: ACQUIRE DATA
    # -----------------------------------------------------------------------
    print("\nStep 1. Acquire Data\n")

    dataset_name = "RF_FULGUR_SAMPLE"
    data_path = "./CODE/DATA/" + dataset_name + "/"
    output_path = "./CODE/OUTPUT/"  + dataset_name + "/"
    shape_ext = '.nii.gz'

    if not os.path.exists(output_path):
        os.makedirs(output_path)


    # Load the .nii.gz files
    shape_filenames = sorted(glob.glob(data_path + '*' + shape_ext))
    print('Number of shapes: ' + str(len(shape_filenames)))
    """     
    print('Shape files found:')
    for shape_filename in shape_filenames:
        print(Path(shape_filename).name)
    """
    
    # -----------------------------------------------------------------------
    # Step 2: GROOM - Pre-processing shapes
    # -----------------------------------------------------------------------
    print("\nStep 2. Groom - Data Pre-processing\n")

    groom_dir = output_path + 'groomed/'
    if not os.path.exists(groom_dir):
        os.makedirs(groom_dir)

    # Initialize lists for segmentations and names
    shape_seg_list = []
    shape_names = []

    # Load the segmentations and perform grooming steps
    for shape_filename in tqdm(shape_filenames, desc="Loading and Grooming Shapes"):

        shape_name = shape_filename.split('/')[-1].replace(shape_ext, '')
        shape_names.append(shape_name)
        
        shape_seg = sw.Image(shape_filename)
        shape_seg_list.append(shape_seg)

        iso_value = 0.5
        bounding_box = sw.ImageUtils.boundingBox([shape_seg], iso_value).pad(2)
        shape_seg.crop(bounding_box)
        antialias_iterations = 30
        iso_spacing = [1, 1, 1]
        shape_seg.antialias(antialias_iterations).resample(iso_spacing, sw.InterpolationType.Linear).binarize()
        pad_size = 5
        pad_value = 0
        shape_seg.pad(pad_size, pad_value)
        
    # -----------------------------------------------------------------------
    # Step 3: GROOM - Rigid Transformations
    # -----------------------------------------------------------------------
    print("\nStep 3. Groom - Rigid Transformations\n")

    print("Finding reference image...")
    ref_index = sw.find_reference_image_index(shape_seg_list)
    ref_seg = shape_seg_list[ref_index].write(groom_dir + 'reference.nii.gz')
    ref_name = shape_names[ref_index]
    print("Reference found: " + ref_name)
    
    # Construct the directory and filename using os.path.join
    transform_dir = os.path.join(groom_dir, 'rigid_transforms')
    if not os.path.exists(transform_dir):
        os.makedirs(transform_dir)

    rigid_transforms = []
    for shape_seg, shape_name in tqdm(zip(shape_seg_list, shape_names), desc="Finding Alignment Transforms", total=len(shape_seg_list)):
        iso_value = 0.5
        icp_iterations = 100
        rigid_transform = shape_seg.createRigidRegistrationTransform(
            ref_seg, iso_value, icp_iterations)
        rigid_transform = sw.utils.getVTKtransform(rigid_transform)
        rigid_transforms.append(rigid_transform) 
        
        # Ensure shape_name and ref_name are valid by using os.path.basename
        shape_base_name = os.path.basename(shape_name)
        ref_base_name = os.path.basename(ref_name)

        # Save the transform matrix
        transform_filename = os.path.join(transform_dir, f'{shape_base_name}_to_{ref_base_name}_transform.txt')
        np.savetxt(transform_filename, rigid_transform)
                
        shape_seg.antialias(antialias_iterations).computeDT(0).gaussianBlur(1.5)
    
    print("Saving distance transforms..")
    groomed_files = sw.utils.save_images(
        groom_dir + 'distance_transforms/', 
        shape_seg_list, 
        shape_names, 
        extension='nii.gz', 
        compressed=True, 
        verbose=False
        )

    # Adjust the input for mesh creation
    domain_type, groomed_files = sw.data.get_optimize_input(groomed_files, args.mesh_mode)

    print("\nStep 4. Optimize - Particle Based Optimization\n")
        
    # -----------------------------------------------------------------------
    # Step 4: OPTIMIZE - Particle Based Optimization
    # -----------------------------------------------------------------------

    project_location = output_path
    if not os.path.exists(project_location):
        os.makedirs(project_location)
    
    subjects = []
    number_domains = 1
    for i in tqdm(range(len(shape_seg_list)), desc="Setting Up Subjects"):
        subject = sw.Subject()
        subject.set_number_of_domains(number_domains)
        rel_seg_files = sw.utils.get_relative_paths([os.getcwd() + '/' + shape_filenames[i]], project_location)
        subject.set_original_filenames(rel_seg_files)
        rel_groom_files = sw.utils.get_relative_paths([os.getcwd() + '/' + groomed_files[i]], project_location)
        subject.set_groomed_filenames(rel_groom_files)
        transform = [rigid_transforms[i].flatten()]
        subject.set_groomed_transforms(transform)
        subjects.append(subject)
    
    project = sw.Project()
    project.set_subjects(subjects)
    parameters = sw.Parameters()

    parameter_dictionary = {
        "number_of_particles": 128,
        "use_normals": 0,
        "normals_strength": 10.0,
        "checkpointing_interval": 1000,
        "keep_checkpoints": 0,
        "iterations_per_split": 1000,
        "optimization_iterations": 1000,
        "starting_regularization": 10,
        "ending_regularization": 1,
        "relative_weighting": 1,
        "initial_relative_weighting": 0.05,
        "procrustes_interval": 0,
        "procrustes_scaling": 0,
        "save_init_splits": 0,
        "verbosity": 0
    }

    if args.tiny_test:
        parameter_dictionary["number_of_particles"] = 32
        parameter_dictionary["optimization_iterations"] = 25

    if not args.use_single_scale:
        parameter_dictionary["multiscale"] = 1
        parameter_dictionary["multiscale_particles"] = 32

    for key in parameter_dictionary:
        parameters.set(key, sw.Variant([parameter_dictionary[key]]))
    
    project.set_parameters("optimize", parameters)
    spreadsheet_file = output_path + dataset_name + "_" + args.option_set + ".swproj"
    project.save(spreadsheet_file)

    optimize_cmd = ('shapeworks optimize --progress --name ' + spreadsheet_file).split()
    subprocess.check_call(optimize_cmd)

    sw.utils.check_results(args, spreadsheet_file)
    
    end_time = time.time()
    total_time = end_time - start_time
    minutes, seconds = divmod(total_time, 60)
    print("Total time: {} minutes {:.2f} seconds".format(int(minutes), seconds))

    # -----------------------------------------------------------------------
    # Step 5: Open ShapeWorks
    # -----------------------------------------------------------------------
    print("\nStep 5: Analysis - Launch ShapeWorksStudio")
    
    analyze_cmd = ('ShapeWorksStudio ' + spreadsheet_file).split()
    subprocess.check_call(analyze_cmd)


if __name__ == "__main__":
    class Args:
        tiny_test = False
        use_single_scale = 0
        mesh_mode = True
        num_subsample = 10
        use_subsample = False
        option_set = 'default'
        verify = False

    args = Args()
    Run_Pipeline(args)
