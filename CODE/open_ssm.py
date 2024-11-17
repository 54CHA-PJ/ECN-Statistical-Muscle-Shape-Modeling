import os
import sys
import glob
import numpy as np
import pyvista as pv

def plot_mesh_with_particles(dataset_folder, dataset_name, N):
    """
    Plots the mesh number N with its associated particle system.

    Parameters:
    - dataset_folder: Path to the dataset folder inside the output folder.
    - N: The index (starting from 0) of the mesh to plot.
    """
    # Construct the paths
    meshes_dir = os.path.join(dataset_folder, 'groomed', 'meshes')
    particles_dir = os.path.join(dataset_folder, dataset_name + '_default_particles')

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

def plot_all_meshes_with_particles(dataset_folder, dataset_name):
    """
    Plots all meshes with their particle systems in the same plot.
    Synchronizes the view across all plots.

    Parameters:
    - dataset_folder: Path to the dataset folder inside the output folder.
    - dataset_name: Name of the dataset.
    """
    # Construct the paths
    meshes_dir = os.path.join(dataset_folder, 'groomed', 'meshes')
    particles_dir = os.path.join(dataset_folder, dataset_name + '_default_particles')

    # Get the list of mesh files
    mesh_files = sorted(glob.glob(os.path.join(meshes_dir, '*.vtk')))

    n_meshes = len(mesh_files)
    if n_meshes == 0:
        print("No meshes found.")
        return

    # Determine the grid size for subplots
    ncols = int(np.ceil(np.sqrt(n_meshes)))
    nrows = int(np.ceil(n_meshes / ncols))

    # Create a PyVista Plotter with subplots
    plotter = pv.Plotter(shape=(nrows, ncols), border=False)

    # Loop over the meshes
    for idx, mesh_file in enumerate(mesh_files):
        mesh_name = os.path.basename(mesh_file)
        particle_file = os.path.join(particles_dir, os.path.splitext(mesh_name)[0] + '_local.particles')

        if not os.path.exists(particle_file):
            print(f"Particle file {particle_file} does not exist. Skipping.")
            continue

        # Load the mesh and particles
        mesh = pv.read(mesh_file)
        particles = np.loadtxt(particle_file)

        # Select the subplot
        row = idx // ncols
        col = idx % ncols
        plotter.subplot(row, col)

        # Add the mesh and particles
        plotter.add_mesh(mesh, color='lightgray', opacity=0.6)
        plotter.add_points(particles, color='red', point_size=5, render_points_as_spheres=True)

        # Add a title
        plotter.add_text(f"{mesh_name}", font_size=10)

    # Link the views to synchronize camera movements
    plotter.link_views()

    # Show the plotter
    plotter.show()


if __name__ == "__main__":
    
    DATASET = "MULTIPLE_TEST"
    
    DATA_DIR = "CODE/OUTPUT/" + DATASET
    
    plot_mesh_with_particles(DATA_DIR, DATASET, 0)
    
    plot_all_meshes_with_particles(DATA_DIR, DATASET)