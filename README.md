# BGXUP: Advanced Background Remover and Image Upscaler

## About The Project

BGXUP is a powerful desktop application built with `customtkinter` and PyTorch for advanced image processing. The tool provides a user-friendly graphical interface to perform two primary functions:
1.  **Remove backgrounds from images** with high precision, including options for alpha matting for smoother, more accurate edges.
2.  **Upscale images using super-resolution**, which enhances the image quality by a factor of 2x.

This application is designed for both casual users and professionals who need a simple but powerful tool for quick image edits without relying on complex software suites.

## Key Features

* **Interactive Before-and-After Slider**: Visualize the changes in real-time with a dynamic slider that compares the original and processed images.
* **High-Quality Background Removal**: Uses the `rembg` library, which is powered by a `U-2-Net` deep learning model for accurate subject detection.
* **Advanced Alpha Matting**: Fine-tune the background removal with customizable foreground and background thresholds for exceptionally clean edges.
* **Super-Resolution Upscaling**: Integrates the `super-image` library to apply an `EDSR` (Enhanced Deep Super-Resolution) model, doubling the image resolution while preserving detail.
* **Customizable Backgrounds**: Easily change the background of your processed image to a solid color of your choice.
* **One-Click Save**: Save your final image in either PNG (for transparency) or JPG format.
* **Ready-to-Use Executable**: A standalone `.exe` file is provided for Windows users, allowing the application to run without needing to install Python or any dependencies.

## Prerequisites

Before running the application from the source code, ensure you have the following installed:
* Python 3.8 or higher
* pip (Python package installer)

## Installation and Setup

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/faizanfaiz11422/BGRemover-Upscaler-Application.git](https://github.com/faizanfaiz11422/BGRemover-Upscaler-Application.git)
    cd BGRemover-Upscaler-Application.git
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate   # On Windows
    source venv/bin/activate  # On macOS/Linux
    ```

3.  **Install the required libraries:**
    ```bash
    pip install -r requirements.txt
    ```
    Note: A `requirements.txt` file is not included in the provided code snippet, but you can generate one with `pip freeze > requirements.txt` after installing all dependencies.

4.  **Download the `rembg` model:**
    The first time you run the application, the `rembg` library will automatically download the required `u2net.onnx` model. You do not need to do this manually.

## How to Run the Code

1.  Navigate to the project directory.
2.  Run the main Python script:
    ```bash
    python advanced_background_remover.py
    ```

## Example Usage and Results

Here are some examples of the application's functionality.

### Before & After Background Removal

![Before & After Background Removal](https://github.com/faizanfaiz11422/BGRemover-Upscaler-Application/blob/main/Samples/BG_Remove.png)

### Super-Resolution Upscaling

![Super-Resolution Upsclaing](https://github.com/faizanfaiz11422/BGRemover-Upscaler-Application/blob/main/Samples/Upscale.png)

## Ready-to-Use Executable (Windows)

For a seamless experience on Windows, you can use the pre-compiled executable file.

1.  Download the `BGXUP.exe` from the [Releases page](https://github.com/faizanfaiz11422/BGRemover-Upscaler-Application/releases).
2.  Place the executable in a folder of your choice.
3.  Double-click the file to launch the application.

This version is completely standalone and does not require any Python installation. The `u2net.onnx` model is bundled within the executable, so there's no need to manually download it.

## Important Code Snippets

### Core UI Logic (with `customtkinter`)
The `AdvancedBackgroundRemoverApp` class handles the main application window and all widget interactions.
```python
# Create main frame
self.main_frame = customtkinter.CTkFrame(self)
self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

# Create and place widgets
self.create_widgets()
