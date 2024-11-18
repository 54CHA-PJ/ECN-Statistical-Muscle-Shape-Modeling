import os
import glob
import numpy as np
import pyvista as pv

def plot_all_meshes_with_particles_aligned(dataset_folder, dataset_name):
    """
    Plots all meshes with their particle systems in separate subplots.
    Aligns and centers all meshes so that views are consistent and synchronized.

    Parameters:
    - dataset_folder: Path to the dataset folder inside the output folder.
    - dataset_name: Name of the dataset.
    """
    # Construct the paths
    meshes_dir = os.path.join(dataset_folder, 'groomed', 'meshes')
    particles_dir = os.path.join(dataset_folder, f"{dataset_name}_default_particles")

    # Get the list of mesh files
    mesh_files = sorted(glob.glob(os.path.join(meshes_dir, '*.vtk')))

    if not mesh_files:
        print("No meshes found in the specified directory.")
        return

    meshes = []
    particles_list = []
    centers = []

    # Load all meshes and particles, and compute their centers
    for mesh_file in mesh_files:
        mesh_name = os.path.basename(mesh_file)
        particle_file = os.path.join(particles_dir, os.path.splitext(mesh_name)[0] + '_local.particles')

        if not os.path.exists(particle_file):
            print(f"Particle file {particle_file} does not exist. Skipping this mesh.")
            continue

        # Load the mesh
        mesh = pv.read(mesh_file)
        meshes.append(mesh)

        # Load the particles
        particles = np.loadtxt(particle_file)
        particles_list.append(particles)

        # Compute and store the center of the mesh
        centers.append(mesh.center)

    if not meshes:
        print("No valid meshes with corresponding particle files were found.")
        return

    # Compute the average center to align all meshes
    centers = np.array(centers)
    average_center = centers.mean(axis=0)

    # Translate all meshes and particles to the average center
    translated_meshes = []
    translated_particles_list = []
    for mesh, particles in zip(meshes, particles_list):
        translation_vector = average_center - mesh.center
        translated_mesh = mesh.translate(translation_vector, inplace=False)
        translated_meshes.append(translated_mesh)

        translated_particles = particles + translation_vector
        translated_particles_list.append(translated_particles)

    # Determine the grid size for subplots
    n_meshes = len(translated_meshes)
    ncols = int(np.ceil(np.sqrt(n_meshes)))
    nrows = int(np.ceil(n_meshes / ncols))

    # Create a PyVista Plotter with subplots
    plotter = pv.Plotter(shape=(nrows, ncols), border=False)

    # Calculate a common camera position based on all meshes
    # This ensures that all subplots have the same initial view
    combined = pv.MultiBlock(translated_meshes)
    combined_bounds = combined.bounds
    plotter.set_background("white")

    # Loop over the meshes
    for idx, (mesh, particles) in enumerate(zip(translated_meshes, translated_particles_list)):
        mesh_name = os.path.basename(mesh_files[idx])

        # Select the subplot
        row = idx // ncols
        col = idx % ncols
        plotter.subplot(row, col)

        # Add the mesh and particles
        plotter.add_mesh(mesh, color='lightgray', opacity=0.6)
        plotter.add_points(particles, color='red', point_size=5, render_points_as_spheres=True)

        # Add a title
        plotter.add_text(f"{mesh_name}", font_size=10)

        # Optionally, adjust the camera to encompass the mesh
        # This ensures consistency across subplots
        plotter.camera_position = 'xy'

    # Link the views to synchronize camera movements
    plotter.link_views()

    # Optionally, set a global view based on the combined bounds
    plotter.reset_camera()

    # Show the plotter
    plotter.show()


def plot_mesh_with_particles(dataset_folder, dataset_name, N):
    """
    Plots the mesh number N with its associated particle system.

    Parameters:
    - dataset_folder: Path to the dataset folder inside the output folder.
    - N: The index (starting from 0) of the mesh to plot.
    """
    # Construct the paths
    meshes_dir = os.path.join(dataset_folder, 'groomed', 'meshes')
    particles_dir = os.path.join(dataset_folder, f"{dataset_name}_default_particles")

    # Get the list of mesh files
    mesh_files = sorted(glob.glob(os.path.join(meshes_dir, '*.vtk')))

    if N < 0 or N >= len(mesh_files):
        print(f"Invalid mesh number N. There are {len(mesh_files)} meshes.")
        return

    mesh_file = mesh_files[N]
    mesh_name = os.path.basename(mesh_file)

    # Assuming particle files are named similarly to mesh files but with a different extension
    particle_file = os.path.join(particles_dir, os.path.splitext(mesh_name)[0] + '_local.particles')

    if not os.path.exists(particle_file):
        print(f"Particle file {particle_file} does not exist.")
        return

    # Load the mesh
    mesh = pv.read(mesh_file)

    # Load the particles
    particles = np.loadtxt(particle_file)

    # Create a PyVista plotter
    plotter = pv.Plotter()

    # Add the mesh
    plotter.add_mesh(mesh, color='lightgray', opacity=0.6)

    # Add the particles as spheres
    plotter.add_points(particles, color='red', point_size=5, render_points_as_spheres=True)

    # Set plotter properties
    plotter.add_title(f"Mesh: {mesh_name}")
    plotter.show()


if __name__ == "__main__":
    DATASET = "RF_DIASEM"
    DATA_DIR = os.path.join("CODE", "OUTPUT", DATASET)

    # Uncomment the following line to plot a single mesh
    # plot_mesh_with_particles(DATA_DIR, DATASET, 0)

    # Plot all meshes aligned and centered in separate, synchronized subplots
    plot_all_meshes_with_particles_aligned(DATA_DIR, DATASET)
