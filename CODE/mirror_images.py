import os
import shapeworks as sw
import pyvista as pv

def mirror_image(image):
    mirrored_image = image.reflect(axis='x', origin='center')
    return mirrored_image

def plot_meshes(mesh1, mesh2, title1, title2):
    vtk_mesh1 = mesh1.mesh
    vtk_mesh2 = mesh2.mesh
    pv_mesh1 = pv.wrap(vtk_mesh1)
    pv_mesh2 = pv.wrap(vtk_mesh2)
    plotter = pv.Plotter(shape=(1, 2))
    plotter.subplot(0, 0)
    plotter.add_mesh(pv_mesh1, color='red')
    plotter.add_text(title1)
    plotter.subplot(0, 1)
    plotter.add_mesh(pv_mesh2, color='blue')
    plotter.add_text(title2)
    plotter.link_views()
    plotter.show()

if __name__ == "__main__":
    data_dir = "DATA/RF_FULGUR"
    left_path = os.path.join(data_dir, "FULGUR_002_283592_left_label_4.nii.gz")
    right_path = os.path.join(data_dir, "FULGUR_002_283592_right_label_4.nii.gz")
    left_img = sw.Image(left_path)
    right_img = sw.Image(right_path)
    left_mesh = left_img.toMesh()
    right_mesh = right_img.toMesh()
    plot_meshes(left_mesh, right_mesh, "Left Original", "Right Original")
    mirrored_left_img = mirror_image(left_img)
    mirrored_left_mesh = mirrored_left_img.toMesh()
    plot_meshes(mirrored_left_mesh, right_mesh, "Left Mirrored", "Right Original")
