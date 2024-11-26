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

    dataset_name = "RF_TEST_2"
    dataset_paths = [
        ('./CODE/DATA/RF_FULGUR_SAMPLE', 'RFTEST1'),   # FULGUR SAMPLE pt1
        ('./CODE/DATA/RF_FULGUR_SAMPLE_2', 'RFTEST2'), # FULGUR SAMPLE pt2
    ]
    output_path = os.path.abspath(os.path.join("./CODE/OUTPUT/", dataset_name))
    shape_ext = '.nii.gz'

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Load the .nii.gz files
    shape_filenames = []
    dataset_ids = []

    for data_path, dataset_id in dataset_paths:
        files = sorted(glob.glob(os.path.join(data_path, '*' + shape_ext)))
        shape_filenames.extend(files)
        dataset_ids.extend([dataset_id] * len(files))

    print('Number of shapes: ' + str(len(shape_filenames)))

    # -----------------------------------------------------------------------
    # Step 2: GROOM - Pre-processing shapes
    # -----------------------------------------------------------------------
    print("\n----------------------------------------")
    print("Step 2. Groom - Data Pre-processing\n")

    groom_dir = os.path.abspath(os.path.join(output_path, 'groomed'))
    if not os.path.exists(groom_dir):
        os.makedirs(groom_dir)

    shape_seg_list = []
    shape_names = []

    # Load and groom shapes
    for i, shape_filename in enumerate(tqdm(shape_filenames, desc="Loading and Grooming Shapes")):
        dataset_id = dataset_ids[i]
        base_shape_name = os.path.splitext(os.path.basename(shape_filename))[0].replace('.nii', '')
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
    ref_seg_path = os.path.join(groom_dir, 'reference.nii.gz')
    ref_seg.write(ref_seg_path)
    print(f"Reference found: {ref_name} ({ref_seg_path})\n")

    transform_dir = os.path.join(groom_dir, 'rigid_transforms')
    dt_dir = os.path.join(groom_dir, 'distance_transforms')
    mesh_dir = os.path.join(groom_dir, 'meshes')

    os.makedirs(transform_dir, exist_ok=True)
    os.makedirs(dt_dir, exist_ok=True)
    os.makedirs(mesh_dir, exist_ok=True)

    rigid_transforms = []
    groomed_files_dt = []
    groomed_files_mesh = []

    isovalue = 0.5
    icp_iterations = 100

    for i, (shape_seg, shape_name) in enumerate(tqdm(
            zip(shape_seg_list, shape_names),
            desc="Finding Alignment Transforms",
            total=len(shape_seg_list))):

        rigid_transform = shape_seg.createRigidRegistrationTransform(ref_seg, isovalue, icp_iterations)
        rigid_transforms.append(rigid_transform)

        transform_filename = os.path.join(transform_dir, f'{shape_name}_to_{ref_name}_transform.txt')
        np.savetxt(transform_filename, sw.utils.getVTKtransform(rigid_transform))

        dt_filename = os.path.join(dt_dir, shape_name + '.nii.gz')
        shape_seg.antialias(30).computeDT(0).gaussianBlur(1.5).write(dt_filename)
        groomed_files_dt.append(dt_filename)

        mesh_filename = os.path.join(mesh_dir, shape_name + '.vtk')
        shape_mesh = shape_seg.toMesh(isovalue)
        shape_mesh.write(mesh_filename)
        groomed_files_mesh.append(mesh_filename)

    # -----------------------------------------------------------------------
    # Step 4: OPTIMIZE - Particle Based Optimization
    # -----------------------------------------------------------------------
    print("\n----------------------------------------")
    print("Step 4. Optimize - Particle Based Optimization\n")

    project_location = output_path
    os.makedirs(project_location, exist_ok=True)

    subjects = []
    for i in tqdm(range(len(shape_seg_list)), desc="Setting Up Subjects"):
        subject = sw.Subject()
        subject.set_number_of_domains(1)
        subject.set_original_filenames([os.path.abspath(shape_filenames[i])])
        subject.set_groomed_filenames([os.path.abspath(groomed_files_dt[i])])
        transform = [rigid_transforms[i].flatten()]
        subject.set_groomed_transforms(transform)
        subjects.append(subject)

    project = sw.Project()
    project.set_subjects(subjects)

    parameters = sw.Parameters()
    parameters.set("number_of_particles", sw.Variant([128]))
    parameters.set("optimization_iterations", sw.Variant([1000]))

    project.set_parameters("optimize", parameters)
    spreadsheet_file = os.path.join(output_path, dataset_name + "_" + args.option_set + ".swproj")
    project.save(spreadsheet_file)

    optimize_cmd = ['shapeworks', 'optimize', '--progress', '--name', spreadsheet_file]
    subprocess.check_call(optimize_cmd, cwd=project_location)

    """     
    # -----------------------------------------------------------------------
    # Step 5: Open ShapeWorks
    # -----------------------------------------------------------------------
    print("\n----------------------------------------")
    print("Step 5: Analysis - Launch ShapeWorks\n")

    analyze_cmd = ['ShapeWorksStudio', spreadsheet_file]
    subprocess.check_call(analyze_cmd)
    """

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
