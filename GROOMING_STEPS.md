## Grooming Pipeline

---

### I. Image Processing
**Purpose**: Prepare images for consistent and efficient analysis by normalizing them, removing artifacts, and focusing on regions of interest.

#### Bounding Box
- **Purpose**: Reduce image size to object boundaries.
- **Steps**:
    - Compute a tight bounding box around the object using an isovalue of 0.5 to define the object's surface.
    - Pad the bounding box by 2 voxels to ensure the entire object is included.
    - Crop the image to this bounding box using the computed parameters.

#### Antialiasing
- **Purpose**: Smooth the binary segmentation to reduce staircase artifacts from voxelization.
- **Steps**:
    - Apply antialiasing to the image with 30 iterations to smooth object boundaries.

#### Resampling
- **Purpose**: Ensure spacing is equal in all dimensions (isotropic).
- **Steps**:
    - Resample the image to voxel spacing of (1 mm, 1 mm, 1 mm) in x, y, and z directions.
    - Use linear interpolation to set intensity values of the new voxels during resampling.

#### Binarization and Padding
- **Purpose**: Convert the antialiased image into a binary image to distinguish the object from the background. Add padding to limitate boundary effects.
- **Steps**:
    - Apply a threshold to binarize the image, setting voxel values above 0.5 to 1 (object) and below to 0 (background).
    - Pad the image with 5 voxels of background intensity (0) on all sides.

---

### II. Rigid Registration
**Purpose**: Align all images to a common reference frame for comparability across the dataset.

#### Reference Image Selection
- **Purpose**: Choose a representative image as the reference for alignment.
- **Steps**:
    - Use `find_reference_image_index` to identify an image representing the dataset (e.g., median shape).
    - Save the reference image for consistent access. (reference.nii.gz)

#### Rigid Transformation Computation
- **Purpose**: Calculate rigid transformations (translation and rotation) to align each image with the reference.
- **Steps**:
    - For each image:
        - Use `createRigidRegistrationTransform` with the reference image, an isovalue of 0.5, and 100 ICP iterations.
        - Convert the transformation into VTK format for compatibility with other tools.
        - Store the transformation for later application.
        - Save the transformation matrix

---

### III. Distance Transform Computation
**Purpose**: Convert binary images into distance transforms, creating a continuous representation suitable for optimization algorithms.

#### Antialiasing
- **Purpose**: Smooth binary images to reduce discretization artifacts before distance transform computation.
- **Steps**:
    - Apply antialiasing again with 30 iterations to ensure smooth object surfaces.

#### Distance Transform
- **Purpose**: Compute the signed distance field where each voxel's value is its shortest distance to the object's surface.
- **Steps**:
    - Use `computeDT` with an isovalue of 0 to calculate the distance transform of antialiased images.

#### Gaussian Blurring
- **Purpose**: Smooth the distance field to reduce noise and enhance stability during optimization.
- **Steps**:
    - Apply Gaussian blur to distance-transformed images with a standard deviation (sigma) of 1.5 voxels.

---

### IV. Saving Groomed Images
**Purpose**: Save processed images for optimization, ensuring data is organized and accessible.

#### Steps
- Save each processed image to the `distance_transforms` directory within the grooming folder.
- Name files appropriately using the original shape names and ensure `.nii.gz` extension.
- Compress images if necessary to save disk space.

---

### V. Project Setup for Optimization
**Purpose**: Organize all subjects and associated data into a project for use with the ShapeWorks optimizer.

#### Subject Creation
- **Purpose**: Create a `Subject` object for each image, referencing original and groomed images and transformations.
- **Steps**:
    - Initialize a `Subject` object and set the number of domains (typically 1 for single-object images).
    - Set relative paths for original and groomed images.
    - Attach corresponding rigid transformation for optimization.

#### Project Initialization
- **Purpose**: Compile all subjects into a `Project` object and associate optimization parameters.
- **Steps**:
    - Initialize a `Project` object.
    - Add `Subject` objects to the project.
    - Define and assign optimization parameters under the "optimize" stage.

---

### VI. Setting Optimization Parameters
**Purpose**: Define parameters to guide the particle-based optimization process.

#### Steps
- Create a parameter dictionary with key settings such as:
    - Number of particles (e.g., 128).
    - Number of optimization iterations (e.g., 1000).
    - Regularization parameters.
    - Weighting factors and intervals for optimization.
- Adjust parameters for testing (e.g., fewer particles and iterations for a quick test).
- Convert parameter dictionary to a `Parameters` object compatible with ShapeWorks.
- Assign parameters to the project, specifying the optimization stage.

---

### VII. Saving the Project and Running ShapeWorks CLI
**Purpose**: Save the project to a file and execute the ShapeWorks optimizer via CLI.

#### Saving the Project
- **Purpose**: Store project configuration and data references in a `.swproj` file.
- **Steps**:
    - Use `project.save` to write project data to a file with a meaningful name.

#### Running Optimization
- **Purpose**: Execute the optimization algorithm to generate the statistical shape model.
- **Steps**:
    - Construct a command to run ShapeWorks optimize, specifying the project file.
    - Use `subprocess.check_call` to run the command, starting optimization.

#### Verification (Optional)
- **Purpose**: Optionally check optimization results.
- **Steps**:
    - If verification is enabled (`args.verify` is `True`), call `sw.utils.check_results` with appropriate arguments.

---

### VIII. Analysis
**Purpose**: Launch ShapeWorksStudio for visualization, exploration, and analysis of optimized shapes and statistical models.

#### Steps
- Construct a command to launch ShapeWorksStudio with the saved project file.
- Use `subprocess.check_call` to open the GUI for interactive analysis.

---

### Summary of the Pipeline

1. **Image Processing**: Prepare images by cropping, smoothing, resampling, binarizing, and padding.
2. **Rigid Registration**: Align images to a common reference frame.
3. **Distance Transform Computation**: Create smooth distance transforms for optimization.
4. **Saving Groomed Images**: Store processed images for optimization.
5. **Project Setup**: Organize subjects and parameters into a ShapeWorks project.
6. **Setting Optimization Parameters**: Define optimization settings.
7. **Running Optimization**: Execute ShapeWorks optimizer to compute the shape model.
8. **Analysis**: Use ShapeWorksStudio for visualization and analysis.

---

### Notes on Transformations and Processing

- **Bounding Box**: Focuses on the region of interest.
- **Antialiasing**: Smooths object surfaces to reduce artifacts.
- **Resampling**: Ensures consistent voxel dimensions.
- **Binarization**: Prepares images for distance transform.
- **Padding**: Prevents boundary issues in later analyses.
- **Rigid Registration**: Aligns shapes for statistical comparison.
- **Distance Transform and Gaussian Blurring**: Creates continuous shape representations.
- **Project Configuration**: Essential for optimizer interpretation and processing.
- **Optimization Parameters**: Control algorithm behavior and convergence.

By meticulously preparing and processing images, this pipeline ensures ShapeWorks' shape analysis is accurate and meaningful, yielding insights into anatomical structures.
