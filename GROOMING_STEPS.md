## Grooming Pipeline

---

### I. Image Processing
**Purpose**: Prepare images for analysis by normalizing, removing artifacts, and focusing on regions of interest.

#### Steps
- **Bounding Box**:
  - Compute a tight bounding box around the object using isovalue 0.5.
  - Pad the bounding box by 2 voxels.
  - Crop the image to the bounding box.
- **Antialiasing**:
  - Apply antialiasing with 30 iterations.
- **Resampling**:
  - Resample the image to isotropic voxel spacing of (1 mm, 1 mm, 1 mm).
  - Use linear interpolation for resampling.
- **Binarization and Padding**:
  - Binarize the image, setting voxel values above 0.5 to 1 (object) and below to 0 (background).
  - Pad the image with 5 voxels of background intensity (0) on all sides.

---

### II. Rigid Registration
**Purpose**: Align all images to a common reference frame.

#### Steps
- **Reference Image Selection**:
  - Use `find_reference_image_index` to select a representative image.
  - Save the reference image as `reference.nii.gz`.
- **Rigid Transformation Computation**:
  - For each image:
    - Compute the rigid transformation to align with the reference using `createRigidRegistrationTransform` with isovalue 0.5, ICP iterations 100.
    - Convert the transformation to VTK format.
    - Store and save the transformation matrix.

---

### III. Distance Transform Computation
**Purpose**: Convert binary images into distance transforms for optimization algorithms.

#### Steps
- **Distance Transform**:
  - Apply antialiasing again with 30 iterations.
  - Compute the distance transform using `computeDT` with isovalue 0.
  - Apply Gaussian blur with sigma 1.5 voxels.

---

### IV. Setting Optimization Parameters
**Purpose**: Define parameters to guide the particle-based optimization process.

#### Steps
- **Parameter Definition**:
  - Create a parameter dictionary with key settings:
    - Number of particles.
    - Number of optimization iterations.
    - Regularization parameters.
    - Weighting factors and intervals for optimization.
- **Adjustment for Testing**:
  - Adjust parameters for quick tests (e.g., fewer particles, fewer iterations).
- **Parameter Assignment**:
  - Convert the parameter dictionary to a `Parameters` object.
  - Assign parameters to the project, specifying the optimization stage.

---

### Recap of Parameters

#### Pre-processing Parameters
- **Bounding Box**:
  - Isovalue: 0.5
  - Padding: 2 voxels
- **Antialiasing**:
  - Iterations: 30
- **Resampling**:
  - Voxel Spacing: (1 mm, 1 mm, 1 mm)
  - Interpolation Type: Linear
- **Binarization**:
  - Threshold: 0.5
- **Padding**:
  - Size: 5 voxels
  - Value: 0 (background intensity)

#### Rigid Registration Parameters
- **Reference Image**:
  - Selected using `find_reference_image_index`
- **Rigid Transformation**:
  - Isovalue: 0.5
  - ICP Iterations: 100

#### Distance Transform Parameters
- **Antialiasing**:
  - Iterations: 30
- **Distance Transform**:
  - Isovalue: 0 (defines interface between foreground and background)
- **Gaussian Blur**:
  - Sigma: 1.5 voxels

### Optimization Parameters

#### Particle-Based Optimization Settings
- **number_of_particles**: 128 — Number of particles (landmarks) per shape surface.
- **use_normals**: 0 — Use (1) or ignore (0) surface normals.
- **normals_strength**: 10.0 — Influence of normals when enabled; higher values increase alignment weight.
- **checkpointing_interval**: 1000 — Iterations between checkpoint saves, allowing resume points.
- **keep_checkpoints**: 0 — Keep all (1) or latest (0) checkpoint.
- **iterations_per_split**: 1000 — Iterations post each particle split in multiscale optimization.
- **optimization_iterations**: 1000 — Total iterations for optimization.
- **starting_regularization**: 10 — Initial weight for smoothness.
- **ending_regularization**: 1 — Final weight, allowing finer details.
- **relative_weighting**: 1 — Balances correspondence vs. regularization terms.
- **initial_relative_weighting**: 0.05 — Initial balance at start.
- **procrustes_interval**: 0 — Interval for Procrustes alignment; 0 disables it.
- **procrustes_scaling**: 0 — Scale (1) or ignore scaling (0) in Procrustes alignment.
- **save_init_splits**: 0 — Save particle positions after initial splits.
- **verbosity**: 0 — Sets output detail level during optimization.

#### Multiscale Optimization (if enabled)
- **multiscale**: 1 — Enables (1) or disables (0) multiscale optimization.
- **multiscale_particles**: 32 — Initial particles for the first multiscale level.

#### Other Parameters
- **mesh_mode**: True — Defines data type; True for mesh, False for image.
- **num_subsample**: 10 — Number of subjects when subsampling.
- **option_set**: 'default' — Label for option set configuration.
