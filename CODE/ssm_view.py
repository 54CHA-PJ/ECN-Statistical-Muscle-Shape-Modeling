import os
import glob
import numpy as np
import pyvista as pv

def plot_all_meshes_with_particles_aligned(dataset_folder, dataset_name):
    meshes_dir = os.path.join(dataset_folder, 'groomed', 'meshes')
    particles_dir = os.path.join(dataset_folder, f"{dataset_name}_default_particles")
    mesh_files = sorted(glob.glob(os.path.join(meshes_dir, '*.vtk')))
    if not mesh_files:
        print("No meshes found in the specified directory.")
        return
    meshes = []
    particles_list = []
    centers = []
    for mesh_file in mesh_files:
        mesh_name = os.path.basename(mesh_file)
        particle_file = os.path.join(particles_dir, os.path.splitext(mesh_name)[0] + '_local.particles')
        if not os.path.exists(particle_file):
            print(f"Particle file {particle_file} does not exist. Skipping this mesh.")
            continue
        mesh = pv.read(mesh_file)
        meshes.append(mesh)
        particles = np.loadtxt(particle_file)
        particles_list.append(particles)
        centers.append(mesh.center)
    if not meshes:
        print("No valid meshes with corresponding particle files were found.")
        return
    centers = np.array(centers)
    average_center = centers.mean(axis=0)
    translated_meshes = []
    translated_particles_list = []
    for mesh, particles in zip(meshes, particles_list):
        translation_vector = average_center - mesh.center
        translated_mesh = mesh.translate(translation_vector, inplace=False)
        translated_meshes.append(translated_mesh)
        translated_particles = particles + translation_vector
        translated_particles_list.append(translated_particles)
    n_meshes = len(translated_meshes)
    ncols = int(np.ceil(np.sqrt(n_meshes)))
    nrows = int(np.ceil(n_meshes / ncols))
    plotter = pv.Plotter(shape=(nrows, ncols), border=False)
    combined = pv.MultiBlock(translated_meshes)
    combined_bounds = combined.bounds
    plotter.set_background("white")
    for idx, (mesh, particles) in enumerate(zip(translated_meshes, translated_particles_list)):
        mesh_name = os.path.basename(mesh_files[idx])
        row = idx // ncols
        col = idx % ncols
        plotter.subplot(row, col)
        plotter.add_mesh(mesh, color='lightgray', opacity=0.6)
        plotter.add_points(particles, color='red', point_size=5, render_points_as_spheres=True)
        plotter.add_text(f"{mesh_name}", font_size=10)
        plotter.camera_position = 'xy'
    plotter.link_views()
    plotter.reset_camera()
    plotter.show()

def plot_mesh_with_particles(dataset_folder, dataset_name, N):
    meshes_dir = os.path.join(dataset_folder, 'groomed', 'meshes')
    particles_dir = os.path.join(dataset_folder, f"{dataset_name}_default_particles")
    mesh_files = sorted(glob.glob(os.path.join(meshes_dir, '*.vtk')))
    if N < 0 or N >= len(mesh_files):
        print(f"Invalid mesh number N. There are {len(mesh_files)} meshes.")
        return
    mesh_file = mesh_files[N]
    mesh_name = os.path.basename(mesh_file)
    particle_file = os.path.join(particles_dir, os.path.splitext(mesh_name)[0] + '_local.particles')
    if not os.path.exists(particle_file):
        print(f"Particle file {particle_file} does not exist.")
        return
    mesh = pv.read(mesh_file)
    particles = np.loadtxt(particle_file)
    plotter = pv.Plotter()
    plotter.add_mesh(mesh, color='lightgray', opacity=0.6)
    plotter.add_points(particles, color='red', point_size=5, render_points_as_spheres=True)
    plotter.add_title(f"Mesh: {mesh_name}")
    plotter.show()
    
def plot_mesh_without_particles(dataset_folder, dataset_name, N):
    meshes_dir = os.path.join(dataset_folder, 'groomed', 'meshes')
    mesh_files = sorted(glob.glob(os.path.join(meshes_dir, '*.vtk')))
    if N < 0 or N >= len(mesh_files):
        print(f"Invalid mesh number N. There are {len(mesh_files)} meshes.")
        return
    mesh_file = mesh_files[N]
    mesh_name = os.path.basename(mesh_file)
    mesh = pv.read(mesh_file)
    plotter = pv.Plotter()
    plotter.add_mesh(mesh, color='lightgray', opacity=1)
    plotter.add_title(f"Mesh: {mesh_name}")
    plotter.show()

if __name__ == "__main__":
    DATASET = "RF_FULGUR_M_MESH"
    DATA_DIR = os.path.join("CODE", "OUTPUT", DATASET)
    plot_mesh_without_particles(DATA_DIR, DATASET,13)
    # plot_all_meshes_with_particles_aligned(DATA_DIR, DATASET)
    # plot_mesh_with_particles(DATA_DIR, DATASET, 9)
    
