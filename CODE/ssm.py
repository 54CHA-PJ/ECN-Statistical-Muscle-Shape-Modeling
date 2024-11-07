import os
import glob
import subprocess
import shapeworks as sw
from pathlib import Path

def Run_Pipeline(args):
    print("\nStep 1. Acquire Data\n")
    
    """
    Step 1: ACQUIRE DATA
    Load the shapes from the MUSCLES dataset instead of downloading the toy dataset.
    """
    dataset_name = "FULGUR"
    data_path = "./CODE/DATA/label4/"
    shape_ext = '.nii.gz'  # Working with .nii.gz files instead of .nrrd
    output_directory = "OUTPUT/LABEL4/"
    
    # Create output directory
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Load the .nii.gz files
    shape_filenames = sorted(glob.glob(data_path + '*' + shape_ext))
    print('Number of shapes: ' + str(len(shape_filenames)))
    print('Shape files found:')
    for shape_filename in shape_filenames:
        print(Path(shape_filename).name)

    print("\nStep 2. Groom - Data Pre-processing\n")
    """
    Step 2: GROOM - Pre-processing MUSCLES shapes
    """
    groom_dir = output_directory + 'groomed/'
    if not os.path.exists(groom_dir):
        os.makedirs(groom_dir)

    # Initialize lists for segmentations and names
    shape_seg_list = []
    shape_names = []

    # Load the segmentations and perform grooming steps
    for shape_filename in shape_filenames:
        print('Loading: ' + shape_filename)
        shape_name = shape_filename.split('/')[-1].replace(shape_ext, '')
        shape_names.append(shape_name)
        
        shape_seg = sw.Image(shape_filename)
        shape_seg_list.append(shape_seg)

        print("Grooming: " + shape_name)
        iso_value = 0.5
        bounding_box = sw.ImageUtils.boundingBox([shape_seg], iso_value).pad(2)
        shape_seg.crop(bounding_box)
        antialias_iterations = 30
        iso_spacing = [1, 1, 1]
        shape_seg.antialias(antialias_iterations).resample(iso_spacing, sw.InterpolationType.Linear).binarize()
        pad_size = 5
        pad_value = 0
        shape_seg.pad(pad_size, pad_value)
    
    ref_index = sw.find_reference_image_index(shape_seg_list)
    ref_seg = shape_seg_list[ref_index].write(groom_dir + 'reference.nii.gz')
    ref_name = shape_names[ref_index]
    print("Reference found: " + ref_name)

    rigid_transforms = []
    for shape_seg, shape_name in zip(shape_seg_list, shape_names):
        print('Finding alignment transform from ' + shape_name + ' to ' + ref_name)
        iso_value = 0.5
        icp_iterations = 100
        rigid_transform = shape_seg.createRigidRegistrationTransform(
            ref_seg, iso_value, icp_iterations)
        rigid_transform = sw.utils.getVTKtransform(rigid_transform)
        rigid_transforms.append(rigid_transform) 

        print("Converting " + shape_name + " to distance transform")
        shape_seg.antialias(antialias_iterations).computeDT(0).gaussianBlur(1.5)

    groomed_files = sw.utils.save_images(groom_dir + 'distance_transforms/', shape_seg_list, shape_names, extension='nii.gz', compressed=True, verbose=True)

    # Adjust the input for mesh creation
    domain_type, groomed_files = sw.data.get_optimize_input(groomed_files, args.mesh_mode)

    print("\nStep 3. Optimize - Particle Based Optimization\n")
    """
    Step 3: OPTIMIZE - Particle Based Optimization
    """
    project_location = output_directory
    if not os.path.exists(project_location):
        os.makedirs(project_location)
    
    subjects = []
    number_domains = 1
    for i in range(len(shape_seg_list)):
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
    spreadsheet_file = output_directory + dataset_name + "_" + args.option_set + ".swproj"
    project.save(spreadsheet_file)

    optimize_cmd = ('shapeworks optimize --progress --name ' + spreadsheet_file).split()
    subprocess.check_call(optimize_cmd)

    sw.utils.check_results(args, spreadsheet_file)

    print("\nStep 4: Analysis - Launch ShapeWorksStudio")
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
