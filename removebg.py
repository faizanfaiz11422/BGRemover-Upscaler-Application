import customtkinter
from tkinter import filedialog, messagebox, colorchooser
from PIL import Image, ImageTk
from rembg import remove
import os

# Import the super-image library and torch for upscaling
from super_image import EdsrModel, ImageLoader
import torch

# Set the appearance mode and default color theme
customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")


class BeforeAfterSliderFrame(customtkinter.CTkFrame):
    """A custom frame with a canvas to display a before-and-after image slider."""

    def __init__(self, master, width, height, **kwargs):
        super().__init__(master, **kwargs)
        self.width = width
        self.height = height
        self.canvas = customtkinter.CTkCanvas(self, width=self.width, height=self.height, bg="black")
        self.canvas.pack(fill="both", expand=True)

        self.image1_pil = None
        self.image2_pil = None
        self.separator_pos = self.width / 2

        # A strong reference to the image objects to prevent garbage collection
        self.canvas.original_photo_image = None
        self.canvas.processed_photo_image = None

        # Store resized PIL images for cropping
        self.resized_image1_pil = None
        self.resized_image2_pil = None
        self.canvas.cropped_original_photo_image = None
        self.canvas.cropped_processed_photo_image = None

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, event):
        """Handle window resize and re-draw the images."""
        self.width = event.width
        self.height = event.height
        self.canvas.configure(width=self.width, height=self.height)
        self.show_images(self.image1_pil, self.image2_pil)

    def _on_press(self, event):
        """Handle mouse press event on the canvas."""
        self.separator_pos = event.x
        self._redraw_images()

    def _on_drag(self, event):
        """Handle mouse drag event on the canvas."""
        # Get image dimensions and position on the canvas
        if self.resized_image1_pil:
            img_width = self.resized_image1_pil.width
            canvas_left = (self.width - img_width) / 2
            canvas_right = canvas_left + img_width

            # Clamp the separator position to the image boundaries
            self.separator_pos = max(canvas_left, min(event.x, canvas_right))
        else:
            # Fallback to canvas boundaries if no image is loaded
            self.separator_pos = event.x
            if self.separator_pos < 0:
                self.separator_pos = 0
            elif self.separator_pos > self.width:
                self.separator_pos = self.width

        self._redraw_images()

    def _redraw_images(self):
        """Redraw the images and the separator line on the canvas."""
        self.canvas.delete("all")

        if self.resized_image1_pil and self.resized_image2_pil:
            img_width = self.resized_image1_pil.width
            img_height = self.resized_image2_pil.height

            # Calculate image position on canvas
            image_x_offset = (self.width - img_width) / 2

            # Draw the left (processed) side
            crop_right = min(img_width, int(self.separator_pos - image_x_offset))
            if crop_right > 0:
                cropped_image2 = self.resized_image2_pil.crop((0, 0, crop_right, img_height))
                cropped_photo_image2 = ImageTk.PhotoImage(cropped_image2)
                self.canvas.create_image(self.separator_pos, self.height / 2, anchor="e", image=cropped_photo_image2)
                self.canvas.cropped_processed_photo_image = cropped_photo_image2

            # Draw the right (original) side
            crop_left = max(0, int(self.separator_pos - image_x_offset))
            if crop_left < img_width:
                cropped_image1 = self.resized_image1_pil.crop((crop_left, 0, img_width, img_height))
                cropped_photo_image1 = ImageTk.PhotoImage(cropped_image1)
                self.canvas.create_image(self.separator_pos, self.height / 2, anchor="w", image=cropped_photo_image1)
                self.canvas.cropped_original_photo_image = cropped_photo_image1
        elif self.resized_image1_pil:
            # Draw only the original image if no processed image is available
            self.canvas.create_image(self.width / 2, self.height / 2, anchor="center",
                                     image=self.canvas.original_photo_image)

        # Draw the vertical line for the slider
        self.canvas.create_line(self.separator_pos, 0, self.separator_pos, self.height, fill="white", width=2)

    def show_images(self, pil_image1, pil_image2=None):
        """Load and display the before and after images."""
        self.canvas.delete("all")

        # Explicitly clear all previous image references
        self.image1_pil = None
        self.image2_pil = None
        self.resized_image1_pil = None
        self.resized_image2_pil = None
        self.canvas.original_photo_image = None
        self.canvas.processed_photo_image = None
        self.canvas.cropped_original_photo_image = None
        self.canvas.cropped_processed_photo_image = None

        self.image1_pil = pil_image1
        self.image2_pil = pil_image2

        # Resize images to fit canvas
        def resize_image(pil_img):
            if not pil_img:
                return None
            img_width, img_height = pil_img.size
            ratio = min(self.width / img_width, self.height / img_height)
            new_size = (int(img_width * ratio), int(img_height * ratio))
            if new_size[0] == 0 or new_size[1] == 0:
                return None
            resized_img = pil_img.resize(new_size, Image.LANCZOS)
            return resized_img

        self.resized_image1_pil = resize_image(pil_image1)
        self.resized_image2_pil = resize_image(pil_image2)

        # Convert to CTkImage and store references
        if self.resized_image1_pil:
            self.canvas.original_photo_image = ImageTk.PhotoImage(self.resized_image1_pil)
        if self.resized_image2_pil:
            self.canvas.processed_photo_image = ImageTk.PhotoImage(self.resized_image2_pil)

        self.separator_pos = self.width / 2

        self._redraw_images()


class AdvancedBackgroundRemoverApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # Configure the main window
        self.title("FLüXiS")
        self.geometry("1024x768")
        self.resizable(True, True)

        self.input_file_path = None
        self.input_image_pil = None
        self.current_processed_image_transparent = None
        self.final_image_to_save = None
        self.background_color = None

        # Create main frame
        self.main_frame = customtkinter.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Create and place widgets
        self.create_widgets()

    def create_widgets(self):
        """Creates all the widgets for the application's GUI."""
        # Header Label
        header_label = customtkinter.CTkLabel(
            self.main_frame,
            text="Advanced Background Remover and Upscaler",
            font=customtkinter.CTkFont(size=28, weight="bold")
        )
        header_label.pack(pady=(10, 20))

        # Action Buttons Frame
        action_frame = customtkinter.CTkFrame(self.main_frame, fg_color="transparent")
        action_frame.pack(pady=10)

        browse_button = customtkinter.CTkButton(
            action_frame,
            text="Browse Image",
            command=self.browse_image
        )
        browse_button.pack(side="left", padx=10)

        self.remove_bg_button = customtkinter.CTkButton(
            action_frame,
            text="Remove Background",
            command=self.remove_background,
            state="disabled"
        )
        self.remove_bg_button.pack(side="left", padx=10)

        # Upscaling options with clearer labels
        self.upscale_option_menu = customtkinter.CTkOptionMenu(
            action_frame,
            values=["No Upscaling", "2x Super-Resolution Upscaling"],
            command=self.upscale_image,
            state="disabled"
        )
        self.upscale_option_menu.pack(side="left", padx=10)

        self.save_button = customtkinter.CTkButton(
            action_frame,
            text="Save Processed Image",
            command=self.save_image,
            state="disabled"
        )
        self.save_button.pack(side="left", padx=10)

        # Options and color preview frame
        options_frame = customtkinter.CTkFrame(self.main_frame, fg_color="transparent")
        options_frame.pack(pady=10, padx=10)

        bg_color_button = customtkinter.CTkButton(
            options_frame,
            text="Select Background Color",
            command=self.select_background_color
        )
        bg_color_button.pack(side="left", padx=20, pady=10)

        self.color_preview = customtkinter.CTkCanvas(
            options_frame,
            width=20, height=20,
            bg="black"
        )
        self.color_preview.pack(side="left", padx=(0, 20))
        self.color_preview_rect = self.color_preview.create_rectangle(0, 0, 20, 20, fill="", outline="")

        # New frame for advanced background removal options
        advanced_options_frame = customtkinter.CTkFrame(self.main_frame)
        advanced_options_frame.pack(pady=10, padx=10, fill="x")

        # Alpha Matting Checkbox
        self.alpha_matting_var = customtkinter.StringVar(value="off")
        self.alpha_matting_checkbox = customtkinter.CTkCheckBox(
            advanced_options_frame,
            text="Enable Alpha Matting (for smoother edges)",
            command=self.toggle_alpha_matting_options,
            variable=self.alpha_matting_var,
            onvalue="on",
            offvalue="off"
        )
        self.alpha_matting_checkbox.pack(pady=(10, 5), padx=20, anchor="w")

        # Alpha Matting Thresholds and Erode Size Sliders
        self.alpha_matting_frame = customtkinter.CTkFrame(advanced_options_frame)
        # Initially hidden

        self.foreground_threshold_label = customtkinter.CTkLabel(self.alpha_matting_frame,
                                                                 text="Foreground Threshold: 240")
        self.foreground_threshold_label.pack(pady=(5, 0), padx=20, anchor="w")
        self.foreground_threshold_slider = customtkinter.CTkSlider(
            self.alpha_matting_frame, from_=0, to=255, command=self.update_fg_threshold_label
        )
        self.foreground_threshold_slider.set(240)
        self.foreground_threshold_slider.pack(pady=(0, 10), padx=20, fill="x")

        self.background_threshold_label = customtkinter.CTkLabel(self.alpha_matting_frame,
                                                                 text="Background Threshold: 10")
        self.background_threshold_label.pack(pady=(5, 0), padx=20, anchor="w")
        self.background_threshold_slider = customtkinter.CTkSlider(
            self.alpha_matting_frame, from_=0, to=255, command=self.update_bg_threshold_label
        )
        self.background_threshold_slider.set(10)
        self.background_threshold_slider.pack(pady=(0, 10), padx=20, fill="x")

        self.erode_size_label = customtkinter.CTkLabel(self.alpha_matting_frame, text="Erode Size: 10")
        self.erode_size_label.pack(pady=(5, 0), padx=20, anchor="w")
        self.erode_size_slider = customtkinter.CTkSlider(
            self.alpha_matting_frame, from_=0, to=50, command=self.update_erode_size_label
        )
        self.erode_size_slider.set(10)
        self.erode_size_slider.pack(pady=(0, 10), padx=20, fill="x")

        # Status Label and Progress Bar
        self.status_label = customtkinter.CTkLabel(
            self.main_frame,
            text="Please select an image.",
            text_color="gray"
        )
        self.status_label.pack(pady=(5, 10))

        self.progress_bar = customtkinter.CTkProgressBar(self.main_frame, width=300)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(0, 10))
        self.progress_bar.pack_forget()

        # Image preview frame, now a single slider frame
        self.slider_frame = BeforeAfterSliderFrame(self.main_frame, width=800, height=600)
        self.slider_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def toggle_alpha_matting_options(self):
        """Show or hide the alpha matting sliders based on checkbox state."""
        if self.alpha_matting_var.get() == "on":
            self.alpha_matting_frame.pack(pady=10, padx=10, fill="x")
        else:
            self.alpha_matting_frame.pack_forget()

    def update_fg_threshold_label(self, value):
        self.foreground_threshold_label.configure(text=f"Foreground Threshold: {int(value)}")

    def update_bg_threshold_label(self, value):
        self.background_threshold_label.configure(text=f"Background Threshold: {int(value)}")

    def update_erode_size_label(self, value):
        self.erode_size_label.configure(text=f"Erode Size: {int(value)}")

    def _update_display(self):
        """Helper method to update the displayed image and save button state."""
        if not self.current_processed_image_transparent:
            self.final_image_to_save = None
            self.slider_frame.show_images(self.input_image_pil)
            self.save_button.configure(state="disabled")
            return

        # Apply the background color to the current transparent image
        if self.background_color:
            colored_bg = Image.new("RGBA", self.current_processed_image_transparent.size, self.background_color)
            self.final_image_to_save = Image.alpha_composite(colored_bg, self.current_processed_image_transparent)
        else:
            self.final_image_to_save = self.current_processed_image_transparent.copy()

        self.slider_frame.show_images(self.input_image_pil, self.final_image_to_save)
        self.save_button.configure(state="normal")

    def browse_image(self):
        """Allows the user to select an image file and displays it."""
        file_path = filedialog.askopenfilename(
            title="Select an Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.webp")]
        )
        if file_path:
            try:
                # Store the file path and image data
                self.input_file_path = file_path
                self.input_image_pil = Image.open(file_path).convert("RGBA")
                self.current_processed_image_transparent = self.input_image_pil.copy()
                self.final_image_to_save = None

                self._update_display()

                self.status_label.configure(text=f"Image loaded: {os.path.basename(file_path)}", text_color="green")
                self.remove_bg_button.configure(state="normal")
                self.upscale_option_menu.set("No Upscaling")
                self.upscale_option_menu.configure(state="normal")


            except Exception as e:
                messagebox.showerror("Error", f"Failed to open image: {e}")
                self.status_label.configure(text="Please select an image.", text_color="gray")
                self.remove_bg_button.configure(state="disabled")
                self.save_button.configure(state="disabled")
                self.upscale_option_menu.configure(state="disabled")

    def remove_background(self):
        """Removes the background from the selected image."""
        if not self.input_image_pil:
            messagebox.showwarning("Warning", "Please select an image first.")
            return

        self.status_label.configure(text="Removing background...", text_color="orange")
        self.progress_bar.pack()
        self.progress_bar.start()
        self.update()

        try:
            # Get settings from UI
            alpha_matting = self.alpha_matting_var.get() == "on"
            alpha_matting_foreground_threshold = int(self.foreground_threshold_slider.get()) if alpha_matting else 240
            alpha_matting_background_threshold = int(self.background_threshold_slider.get()) if alpha_matting else 10
            alpha_matting_erode_size = int(self.erode_size_slider.get()) if alpha_matting else 10

            # The core background removal logic
            output_image = remove(
                self.input_image_pil,
                alpha_matting=alpha_matting,
                alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
                alpha_matting_background_threshold=alpha_matting_background_threshold,
                alpha_matting_erode_size=alpha_matting_erode_size
            )
            self.current_processed_image_transparent = output_image

            self._update_display()

            self.status_label.configure(text="Background removed successfully!", text_color="green")
        except Exception as e:
            messagebox.showerror("Processing Error", f"An error occurred during background removal: {e}")
            self.status_label.configure(text="Removal failed.", text_color="red")
        finally:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()

    def upscale_image(self, choice):
        """Upscales the processed image based on the selected option."""
        if not self.current_processed_image_transparent:
            messagebox.showwarning("Warning", "Please load an image first.")
            self.upscale_option_menu.set("No Upscaling")
            return

        if choice == "No Upscaling":
            self._update_display()
            return

        self.status_label.configure(text=f"Upscaling image with '{choice}'...", text_color="orange")
        self.progress_bar.pack()
        self.progress_bar.start()
        self.update()

        try:
            image_to_upscale = self.current_processed_image_transparent

            # Load the 2x model
            model = EdsrModel.from_pretrained('eugenesiow/edsr-base', scale=2)

            # Convert PIL image to tensor
            # Note: The model is trained on RGB, so we convert before processing.
            inputs = ImageLoader.load_image(image_to_upscale.convert("RGB"))

            # Perform upscaling
            with torch.no_grad():
                outputs = model(inputs)

            # Corrected logic: Convert output tensor back to PIL Image
            # The tensor is in C, H, W format. We need to permute it to H, W, C for PIL.
            upscaled_rgb_tensor = outputs.squeeze(0).permute(1, 2, 0)
            upscaled_rgb_image = Image.fromarray(
                torch.clamp(upscaled_rgb_tensor.mul(255).round(), 0, 255).byte().cpu().numpy()
            )

            # Restore alpha channel from original image, if it existed
            if 'A' in image_to_upscale.getbands():
                alpha_channel = image_to_upscale.getchannel('A')
                upscaled_alpha = alpha_channel.resize(upscaled_rgb_image.size, Image.LANCZOS)
                upscaled_rgb_image.putalpha(upscaled_alpha)

            self.current_processed_image_transparent = upscaled_rgb_image

            self._update_display()

            self.status_label.configure(text="Image upscaled successfully with Super-Resolution!", text_color="green")
        except OSError as e:
            # Handle the specific error where the model fails to load.
            messagebox.showerror("Processing Error",
                                 f"An error occurred during upscaling: Failed to load model. Please check your internet connection or try again later.")
            self.status_label.configure(text="Upscaling failed.", text_color="red")
        except Exception as e:
            messagebox.showerror("Processing Error", f"An error occurred during upscaling: {e}")
            self.status_label.configure(text="Upscaling failed.", text_color="red")
        finally:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()

    def select_background_color(self):
        """Allows the user to choose a background color."""
        color_code = colorchooser.askcolor(title="Choose background color")
        if color_code:
            self.background_color = color_code[1]
            self.color_preview.itemconfig(self.color_preview_rect, fill=self.background_color)

            self._update_display()

    def apply_background_color(self, image_pil):
        """Applies the selected background color to a PIL image."""
        if self.background_color and image_pil:
            colored_bg = Image.new("RGBA", image_pil.size, self.background_color)
            colored_bg.paste(image_pil, (0, 0), image_pil)
            return colored_bg
        return image_pil

    def save_image(self):
        """Saves the current processed image to a file."""
        if not self.final_image_to_save:
            messagebox.showwarning("Warning", "No image to save. Please process an image first.")
            return

        if self.input_file_path:
            base_name = os.path.basename(self.input_file_path)
            file_name_without_ext = os.path.splitext(base_name)[0]
            initial_file_name = file_name_without_ext + "-processed.png"
        else:
            initial_file_name = "processed_image.png"

        save_path = filedialog.asksaveasfilename(
            title="Save Processed Image",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPG files", "*.jpg"), ("All files", "*.*")],
            initialfile=initial_file_name
        )
        if save_path:
            try:
                # Convert to RGB if saving as JPG/JPEG and a background color is set
                image_to_save = self.final_image_to_save
                if self.background_color and (
                        save_path.lower().endswith('.jpg') or save_path.lower().endswith('.jpeg')):
                    image_to_save = image_to_save.convert("RGB")

                image_to_save.save(save_path)
                self.status_label.configure(text=f"Image saved successfully!", text_color="green")
                messagebox.showinfo("Success", "Image saved successfully!")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save image: {e}")
                self.status_label.configure(text="Saving failed.", text_color="red")


if __name__ == "__main__":
    app = AdvancedBackgroundRemoverApp()
    app.mainloop()
