# Import necessary libraries
import shapeworks as sw
import glob
import numpy as np
import os
import shutil

# Function to mirror the image along the x-axis with proper scaling
def mirror_image(image):
    # Get the image data as a numpy array
    image_data = image.toArray()
    
    # Flip the data along the x-axis (axis=0)
    mirrored_data = np.flip(image_data, axis=2)
    
    # Create a new Shapeworks Image from the flipped data
    mirrored_image = sw.Image(mirrored_data.astype(np.float32))
    
    # Copy the spacing from the original image
    mirrored_image.setSpacing(image.spacing())
    
    # Adjust the origin to account for the flip
    original_origin = image.origin()
    spacing = image.spacing()
    dims = image.dims()
    
    # Calculate the new origin
    new_origin = list(original_origin)
    new_origin[0] = original_origin[0] + (dims[0] - 1) * spacing[0]
    mirrored_image.setOrigin(new_origin)
    
    return mirrored_image

# Function to flip specified images and create a new dataset
def flip_and_create_dataset(dataset_path, files_to_flip):
    # Create the output directory name by adding "_M" to the dataset path
    output_path = dataset_path + "_M"
    
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_path):
        os.makedirs(output_path)
        print(f"Created output directory: {output_path}")
    else:
        print(f"Output directory already exists: {output_path}")
    
    # Get all image files in the dataset path
    all_images = glob.glob(os.path.join(dataset_path, "*.nii.gz"))
    
    print(f"Processing {len(all_images)} images:")
    
    for image_path in all_images:
        # Get the base filename
        filename = os.path.basename(image_path)
        
        # Determine the output path for the image
        output_image_path = os.path.join(output_path, filename)
        
        if image_path in files_to_flip:
            print(f"Flipping image: {filename}")
            # Load the image
            image = sw.Image(image_path)
            # Flip the image
            mirrored_image = mirror_image(image)
            # Save the flipped image
            mirrored_image.write(output_image_path)
        else:
            print(f"Copying image: {filename}")
            # Copy the image to the output directory
            shutil.copy(image_path, output_image_path)
    
    print("Dataset creation complete.")

# Example usage:
if __name__ == "__main__":
    # Define the dataset path
    DATASET_PATH = "./CODE/DATA/RF_FULGUR_PRED"
    # Define the list of files to flip (full paths)
    # For example, all files containing "left" in their filename
    all_images = glob.glob(os.path.join(DATASET_PATH, "*.nii.gz"))
    files_to_flip = [image_path for image_path in all_images if "left" in os.path.basename(image_path)]
    # Call the function
    flip_and_create_dataset(DATASET_PATH, files_to_flip)