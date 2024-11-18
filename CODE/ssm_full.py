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
    print("\n----------------------------------------")
    print("Step 1. Acquire Data\n")

    dataset_name = "RF_FULGUR_FULL"
    dataset_paths = [
        ('./CODE/DATA/RF_FULGUR', 'RF'),
        ('./CODE/DATA/RF_FULGUR_PRED', 'RFP'),
        # ('./CODE/DATA/RF_DIASEM', 'RFDIA'),
    ]
    output_path = os.path.abspath(os.path.join("./CODE/OUTPUT/", dataset_name))
    shape_ext = '.nii.gz'

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Load the .nii.gz files
    shape_filenames = []  # List of filenames
    dataset_ids = []      # Corresponding dataset identifiers

    for data_path, dataset_id in dataset_paths:
        files = sorted(glob.glob(os.path.join(data_path, '*' + shape_ext)))
        shape_filenames.extend(files)
        dataset_ids.extend([dataset_id]*len(files))

    print('Number of shapes: ' + str(len(shape_filenames)))

    # -----------------------------------------------------------------------
    # Step 2: GROOM - Pre-processing shapes
    # -----------------------------------------------------------------------
    print("\n----------------------------------------")
    print("Step 2. Groom - Data Pre-processing\n")

    groom_dir = os.path.abspath(os.path.join(output_path, 'groomed'))
    if not os.path.exists(groom_dir):
        os.makedirs(groom_dir)

    # Initialize lists for segmentations and names
    shape_seg_list = []
    shape_names = []

    # Load the segmentations and perform grooming steps
    for i, shape_filename in enumerate(tqdm(shape_filenames, desc="Loading and Grooming Shapes")):

        dataset_id = dataset_ids[i]
        base_shape_name = os.path.basename(shape_filename).replace(shape_ext, '')
        shape_name = f"{dataset_id}_{base_shape_name}"
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
    print("\n----------------------------------------")
    print("Step 3. Groom - Rigid Transformations\n")

    print("Finding reference image...")
    ref_index = sw.find_reference_image_index(shape_seg_list)
    ref_seg = shape_seg_list[ref_index]
    ref_name = shape_names[ref_index]
    ref_seg.write(os.path.join(groom_dir, 'reference.nii.gz'))
    print("Reference found: " + ref_name + "\n")
    
    # Construct the directory and filename using os.path.join
    transform_dir = os.path.abspath(os.path.join(groom_dir, 'rigid_transforms'))
    if not os.path.exists(transform_dir):
        os.makedirs(transform_dir)

    rigid_transforms = []
    for i, (shape_seg, shape_name) in enumerate(tqdm(zip(shape_seg_list, shape_names), desc="Finding Alignment Transforms", total=len(shape_seg_list))):
        iso_value = 0.5
        icp_iterations = 100
        rigid_transform = shape_seg.createRigidRegistrationTransform(
            ref_seg, iso_value, icp_iterations)
        rigid_transform = sw.utils.getVTKtransform(rigid_transform)
        rigid_transforms.append(rigid_transform) 
        
        # Save the transform matrix
        transform_filename = os.path.join(transform_dir, f'{shape_name}_to_{ref_name}_transform.txt')
        np.savetxt(transform_filename, rigid_transform)
                
        shape_seg.antialias(antialias_iterations).computeDT(0).gaussianBlur(1.5)
    
    print("Saving distance transforms or meshes...\n")
    # Decide the output directory based on mesh_mode
    if args.mesh_mode:
        output_subdir = 'meshes'
        output_extension = '.vtk'
    else:
        output_subdir = 'distance_transforms'
        output_extension = '.nii.gz'

    output_dir = os.path.abspath(os.path.join(groom_dir, output_subdir))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save the groomed files
    groomed_files = []
    for shape_seg, shape_name in zip(shape_seg_list, shape_names):
        output_filename = os.path.join(output_dir, shape_name + output_extension)
        shape_seg.write(output_filename)
        groomed_files.append(output_filename)

    # Adjust the input for mesh creation
    domain_type, groomed_files = sw.data.get_optimize_input(groomed_files, args.mesh_mode)
        
    # -----------------------------------------------------------------------
    # Step 4: OPTIMIZE - Particle Based Optimization
    # -----------------------------------------------------------------------
    print("\n----------------------------------------")
    print("Step 4. Optimize - Particle Based Optimization\n")
    
    project_location = output_path  # Absolute path already ensured
    if not os.path.exists(project_location):
        os.makedirs(project_location)
    
    subjects = []
    number_domains = 1
    for i in tqdm(range(len(shape_seg_list)), desc="Setting Up Subjects"):
        subject = sw.Subject()
        subject.set_number_of_domains(number_domains)
        abs_shape_filename = os.path.abspath(shape_filenames[i])
        # Use absolute paths
        subject.set_original_filenames([abs_shape_filename])
        # Use the adjusted groomed_files[i] with absolute paths
        groomed_file = os.path.abspath(groomed_files[i])
        subject.set_groomed_filenames([groomed_file])
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
    spreadsheet_file = os.path.join(output_path, dataset_name + "_" + args.option_set + ".swproj")
    project.save(spreadsheet_file)

    # Ensure that the shapeworks command is executed in the correct directory
    optimize_cmd = ['shapeworks', 'optimize', '--progress', '--name', spreadsheet_file]
    subprocess.check_call(optimize_cmd, cwd=project_location)

    sw.utils.check_results(args, spreadsheet_file)
    
    end_time = time.time()
    total_time = end_time - start_time
    minutes, seconds = divmod(total_time, 60)
    print("Total time: {} minutes {:.2f} seconds".format(int(minutes), seconds))

    # -----------------------------------------------------------------------
    # Step 5: Open ShapeWorks
    # -----------------------------------------------------------------------
    print("\n----------------------------------------")
    print("Step 5: Analysis - Launch ShapeWorks\n")
    
    analyze_cmd = ['ShapeWorksStudio', spreadsheet_file]
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
