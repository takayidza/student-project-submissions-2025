import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import cv2
import time
import threading
from typing import Optional, Callable, Dict, Any
import logging
import numpy as np
import ctypes
from modules.coodinates import CoordinateManager

logger = logging.getLogger(__name__)

class SpeedEstimatorGUI:
    def __init__(self, root: tk.Tk, process_frame_callback: Callable):
        """
        Enhanced GUI for the Speed Estimator application.
        
        Args:
            root: The tkinter root window
            process_frame_callback: Callback function that processes video frames
        """
        self.root = root
        self.root.title("Vehicle Speed Estimator Pro")
        self.root.geometry("1100x700")
        
        self.coord_manager = CoordinateManager()

        # self.video_panel.bind("<Configure>", self._on_panel_resize)
        # Set application icon
        # self.root.iconbitmap("path/to/icon.ico")  # Uncomment and provide icon path
        
        self.video_source: Optional[str] = None
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running: bool = False
        self.process_frame = process_frame_callback
        self.current_frame = None
        self.progress_value = tk.DoubleVar(value=0)
        self.total_frames = 0
        self.processed_frames = 0
        
        # Stats variables
        self.stats = {
            "vehicles_detected": tk.IntVar(value=0),
            "avg_speed": tk.DoubleVar(value=0),
            "max_speed": tk.IntVar(value=0),
            "processing_fps": tk.DoubleVar(value=0)
        }
        
        self._create_widgets()
        self._create_menu()


    def _on_panel_resize(self, event):
        """Handle resizing of the video panel"""
        # Update the display dimensions in the coordinate manager
        self.coord_manager.update_display_size(event.width, event.height)
        
        # Re-display the current frame if available
        if hasattr(self, 'current_frame') and self.current_frame is not None:
            self.display_frame(self.current_frame, redraw=True)

    def _create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Video", command=self.select_video)
        file_menu.add_command(label="Save Results", command=self._save_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Settings", command=self._open_settings)
        tools_menu.add_command(label="View Database", command=self._open_database_viewer)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="User Guide", command=self._show_help)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    

    def get_screen_resolution_windows():
        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
        return screen_width, screen_height

    def set_video_dimensions(self, width, height):
        """Set the original video dimensions"""
        self.coord_manager.update_original_size(width, height)

    def _create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - video display
        left_panel = ttk.Frame(main_container)
        main_container.add(left_panel, weight=3)
        
        # Control buttons frame
        control_frame = ttk.Frame(left_panel)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Control buttons
        self.load_btn = ttk.Button(control_frame, text="Open Video", command=self.select_video)
        self.load_btn.pack(side=tk.LEFT, padx=5)
        
        self.start_btn = ttk.Button(control_frame, text="Start Processing", 
                                   command=self.start_video, state="disabled")
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="Stop", 
                                  command=self.stop_video, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        progress_frame = ttk.Frame(left_panel)
        progress_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Label(progress_frame, text="Processing:").pack(side=tk.LEFT, padx=5)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_value, 
                                         maximum=100, length=300)
        self.progress_bar.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.pack(side=tk.LEFT, padx=5)
        
        # Video display
        video_frame = ttk.LabelFrame(left_panel, text="Video Feed")
        video_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.display_canvas = tk.Canvas(video_frame, bg="black")
        self.display_canvas.pack(fill=tk.BOTH, expand=True)

        self.display_canvas.bind("<Configure>", self._on_panel_resize)
        
        # Right panel - stats and settings
        right_panel = ttk.Frame(main_container)
        main_container.add(right_panel, weight=1)
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(right_panel, text="Statistics")
        stats_frame.pack(side=tk.TOP, fill=tk.BOTH, padx=5, pady=5)
        
        # Stats labels
        stats_grid = [
            ("Vehicles Detected:", self.stats["vehicles_detected"], ""),
            ("Average Speed:", self.stats["avg_speed"], "km/h"),
            ("Maximum Speed:", self.stats["max_speed"], "km/h"),
            ("Processing Speed:", self.stats["processing_fps"], "FPS")
        ]
        
        for i, (label_text, var, unit) in enumerate(stats_grid):
            ttk.Label(stats_frame, text=label_text).grid(row=i, column=0, sticky=tk.W, padx=5, pady=3)
            value_label = ttk.Label(stats_frame, textvariable=var)
            value_label.grid(row=i, column=1, sticky=tk.E, padx=5, pady=3)
            if unit:
                ttk.Label(stats_frame, text=unit).grid(row=i, column=2, sticky=tk.W, pady=3)
        
        # Settings frame
        settings_frame = ttk.LabelFrame(right_panel, text="Settings")
        settings_frame.pack(side=tk.TOP, fill=tk.BOTH, padx=5, pady=5)
        
        # ROI adjustment
        ttk.Label(settings_frame, text="System GUI: Dashboard on browser").pack(anchor=tk.W, padx=5, pady=5)
        
        roi_btn_frame = ttk.Frame(settings_frame)
        roi_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        
        # Log frame
        log_frame = ttk.LabelFrame(right_panel, text="Event Log")
        log_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(log_frame, height=10, width=30, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        log_scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def start_video(self):
        """Start video processing"""
        if not self.video_source:
            messagebox.showerror("Error", "No video selected. Please select a video first.")
            return
            
        if self.is_running:
            return  # Already running
            
        # Open video capture
        self.cap = cv2.VideoCapture(self.video_source)
        if not self.cap.isOpened():
            messagebox.showerror("Error", f"Could not open video: {self.video_source}")
            return
            
        # Update UI elements
        self.is_running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        
        # Start processing in a separate thread
        self.processing_thread = threading.Thread(target=self._process_video, daemon=True)
        self.processing_thread.start()
        
        self._log_event("Video processing started")

    def select_video(self):
        """Open file dialog to select a video file"""
        path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=(
                ("Video files", "*.mp4 *.avi *.mov *.mkv"),
                ("MP4 files", "*.mp4"),
                ("AVI files", "*.avi"),
                ("All files", "*.*")
            )
        )
        if path:
            self.video_source = path
            self.start_btn.config(state="normal")
            self._log_event(f"Video selected: {path}")
            self.status_bar.config(text=f"Video loaded: {path.split('/')[-1]}")
            
            # Get video information
            try:
                cap = cv2.VideoCapture(path)
                self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                # Update coordinate manager with video dimensions
                self.coord_manager.update_original_size(width, height)
                
                cap.release()
                
                self._log_event(f"Video info: {width}x{height} @ {fps}fps, {self.total_frames} frames")
            except Exception as e:
                self._log_event(f"Error reading video metadata: {str(e)}")


    def _process_video(self):
        """Process video frames in a separate thread"""
        try:
            while self.is_running and self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret:
                    # End of video
                    self.root.after(0, self._on_video_complete)
                    break
                    
                # Process frame with callback and update stats
                start_time = time.time()
                processed_frame, stats_update = self.process_frame(frame)
                
                # Update processing FPS
                processing_time = time.time() - start_time
                self.stats["processing_fps"].set(round(1.0 / max(processing_time, 0.001), 1))
                
                # Update statistics based on returned values
                if stats_update:
                    for key, value in stats_update.items():
                        if key in self.stats:
                            self.stats[key].set(value)
                
                # Update the current frame to be displayed in the main thread
                self.current_frame = processed_frame
                
                # Update progress
                self.processed_frames += 1
                progress_pct = min(100, int((self.processed_frames / self.total_frames) * 100)) if self.total_frames > 0 else 0
                self.progress_value.set(progress_pct)
                
                # Use after method to update progress label in the main thread
                self.root.after(0, lambda p=progress_pct: self.progress_label.config(text=f"{p}%"))
                
                # Schedule the frame update in the main thread
                self.root.after(0, self.update_frame_display)
                
                # Sleep to maintain target FPS if processing is faster
                target_frame_time = 1.0 / 30  # Target 30fps display rate
                elapsed = time.time() - start_time
                if elapsed < target_frame_time:
                    time.sleep(target_frame_time - elapsed)
                    
        except Exception as e:
            logger.exception("Error in video processing thread")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Processing error: {str(e)}"))
            self.root.after(0, self.stop_video)

    
    def update_frame_display(self):
        """
        Update the frame display with proper scaling of all elements.
        This method handles drawing and displaying the current frame with all overlays.
        """
        if self.current_frame is None:
            return
            
        # Get the original frame
        original_frame = self.current_frame.copy()
        h, w = original_frame.shape[:2]
        
        # Store original dimensions for reference
        if not hasattr(self, 'original_width'):
            self.original_width = w
            self.original_height = h
            self.coord_manager.update_original_size(w, h)
        
        # Get canvas dimensions
        canvas_width = self.display_canvas.winfo_width()
        canvas_height = self.display_canvas.winfo_height()
        
        # Skip if canvas is not properly sized yet
        if canvas_width <= 1 or canvas_height <= 1:
            self.root.after(100, self.update_frame_display)  # Try again shortly
            return
        
        # Calculate optimal display size (maintaining aspect ratio)
        ratio = min(canvas_width / w, canvas_height / h)
        new_width = int(w * ratio)
        new_height = int(h * ratio)
        
        # Create a copy for drawing overlays (at ORIGINAL size)
        display_frame = original_frame.copy()
        
        # Draw all overlays on the original-sized frame
        
        # 1. Draw ROI if defined
        # Use _draw_all_overlays to draw all UI elements including ROI
        display_frame = self._draw_all_overlays(display_frame)
        
        # NOW resize the fully-annotated frame to the display size
        display_frame = cv2.resize(display_frame, (new_width, new_height))
        
        # Convert to RGB for Tkinter
        display_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        # if hasattr(self, 'roi_points') and self.roi_points and len(self.roi_points) >= 3:
        #     cv2.polylines(
        #         display_frame, 
        #         [np.array(self.roi_points, dtype=np.int32)], 
        #         True,  # Closed polygon
        #         (0, 255, 0),  # Green color
        #         2  # Line thickness
        #     )
        
        # 2. Draw vehicle tracks if available
        # if hasattr(self, 'current_tracks') and self.current_tracks:
        #     for track_id, track_data in self.current_tracks.items():
        #         # Draw bounding box
        #         if 'bbox' in track_data:
        #             x1, y1, x2, y2 = track_data['bbox']
        #             cv2.rectangle(
        #                 display_frame, 
        #                 (x1, y1), 
        #                 (x2, y2), 
        #                 (0, 165, 255),  # Orange color
        #                 2  # Line thickness
        #             )
                    
        #             # Draw ID and speed
        #             speed = track_data.get('speed', 0)
        #             label = f"ID:{track_id} {speed:.1f}km/h"
                    
        #             cv2.putText(
        #                 display_frame, 
        #                 label, 
        #                 (x1, y1 - 10), 
        #                 cv2.FONT_HERSHEY_SIMPLEX, 
        #                 0.5,  # Font scale
        #                 (0, 165, 255),  # Orange color
        #                 2  # Line thickness
        #             )
                
        #         # Draw tracking path if available
        #         if 'path' in track_data and len(track_data['path']) > 1:
        #             points = np.array(track_data['path'], dtype=np.int32)
        #             cv2.polylines(
        #                 display_frame, 
        #                 [points], 
        #                 False,  # Not a closed curve
        #                 (0, 0, 255),  # Red color
        #                 2  # Line thickness
        #             )
        
        # 3. Draw statistics if enabled
        if hasattr(self, 'show_stats') and self.show_stats:
            stats_text = []
            
            if hasattr(self, 'stats'):
                stats_text = [
                    f"Vehicles: {self.stats.get('vehicles_detected', 0)}",
                    f"Avg Speed: {self.stats.get('avg_speed', 0):.1f} km/h",
                    f"Max Speed: {self.stats.get('max_speed', 0)} km/h",
                    f"FPS: {self.stats.get('fps', 0):.1f}"
                ]
                
            y_offset = 30
            for text in stats_text:
                cv2.putText(
                    display_frame,
                    text,
                    (20, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,  # Font scale
                    (255, 255, 255),  # White color
                    2,  # Line thickness
                    cv2.LINE_AA
                )
                y_offset += 30
        
        # NOW resize the fully-annotated frame to the display size
        display_frame = cv2.resize(display_frame, (new_width, new_height))
        
        # Convert to RGB for Tkinter
        display_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PhotoImage
        self.photo = ImageTk.PhotoImage(image=Image.fromarray(display_rgb))
        
        # Clear canvas and center the image
        self.display_canvas.delete("all")
        
        # Calculate position to center the image on the canvas
        x_pos = canvas_width // 2
        y_pos = canvas_height // 2
        
        # Display image centered
        self.display_canvas.create_image(
            x_pos, y_pos, 
            image=self.photo, 
            anchor=tk.CENTER
        )
        
        # Update status if needed
        if hasattr(self, 'cap') and self.cap and hasattr(self, 'frame_count') and hasattr(self, 'total_frames'):
            # Show progress in status bar if available
            progress = int((self.frame_count / max(1, self.total_frames)) * 100)
            if hasattr(self, 'status_bar'):
                self.status_bar.config(
                    text=f"Processing: {progress}% ({self.frame_count}/{self.total_frames})"
                )

    def _draw_all_overlays(self, frame):
        """Draw all overlays with proper scaling"""
        # Make a copy of the frame for drawing
        display_frame = frame.copy()
        
        # Get original frame dimensions
        h, w = display_frame.shape[:2]
        
        # Calculate scaled parameters
        font_scale = self.coord_manager.scale_font_size(0.5)
        line_thickness = max(1, int(self.coord_manager.scale_line_thickness(2)))
        
        # 1. Draw ROI if defined
        if hasattr(self, 'roi_points') and self.roi_points:
            # For ROI, we don't need to transform coordinates here since
            for i, point in enumerate(self.roi_points):
                display_point = self.coord_manager.frame_to_display(point)
                # print(f"ROI point {i}: Original={point}, Display={display_point}")
            # the frame is already in original coordinates
            cv2.polylines(
                display_frame, 
                [np.array(self.roi_points, dtype=np.int32)], 
                True, 
                (0, 255, 0), 
                line_thickness
            )
        
        # 2. Draw vehicle tracking data if available
        if hasattr(self, 'current_tracks') and self.current_tracks:
            for track_id, track_data in self.current_tracks.items():
                # Draw bounding box
                if 'bbox' in track_data:
                    x1, y1, x2, y2 = track_data['bbox']
                    cv2.rectangle(
                        display_frame, 
                        (x1, y1), 
                        (x2, y2), 
                        (0, 165, 255), 
                        line_thickness
                    )
                    
                    # Draw ID and speed
                    speed = track_data.get('speed', 0)
                    label = f"ID:{track_id} {speed:.1f}km/h"
                    
                    # Get optimal font scale based on image size
                    text_size = font_scale
                    
                    cv2.putText(
                        display_frame, 
                        label, 
                        (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        text_size, 
                        (0, 165, 255), 
                        line_thickness
                    )
                
                # Draw tracking path if available
                if 'path' in track_data and len(track_data['path']) > 1:
                    points = np.array(track_data['path'], dtype=np.int32)
                    cv2.polylines(
                        display_frame, 
                        [points], 
                        False, 
                        (0, 0, 255), 
                        max(1, line_thickness - 1)
                    )
        
        # 3. Draw statistics or other overlays as needed
        if hasattr(self, 'show_stats') and self.show_stats:
            # Draw statistics in top left corner
            stats_text = [
                f"Vehicles: {self.stats['vehicles_detected'].get()}",
                f"Avg Speed: {self.stats['avg_speed'].get():.1f} km/h",
                f"Max Speed: {self.stats['max_speed'].get()} km/h",
                f"FPS: {self.stats['processing_fps'].get():.1f}"
            ]
            
            y_offset = 30
            for text in stats_text:
                cv2.putText(
                    display_frame,
                    text,
                    (20, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale,
                    (255, 255, 255),
                    line_thickness,
                    cv2.LINE_AA
                )
                y_offset += 30
        
        return display_frame


    def _on_video_complete(self):
        """Handle video completion"""
        self._log_event("Video processing completed.")
        self.stop_video()
        messagebox.showinfo("Complete", "Video processing has finished.")

    def stop_video(self):
        """Stop video processing"""
        self.is_running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        if self.cap:
            self.cap.release()
            self.cap = None
        self._log_event("Video processing stopped.")
        self.status_bar.config(text="Ready")

    def _log_event(self, message: str):
        """Add a message to the log with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)  # Scroll to the bottom
        logger.info(message)

    # Placeholder methods for menu commands
    def _save_results(self):
        """Save processing results"""
        save_path = filedialog.asksaveasfilename(
            title="Save Results",
            defaultextension=".csv",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*"))
        )
        if save_path:
            self._log_event(f"Results saved to: {save_path}")
            messagebox.showinfo("Success", f"Results saved to: {save_path}")

    def _open_settings(self):
        """Open settings dialog"""
        # This would open a new dialog window with settings
        self._log_event("Settings dialog opened")
        # Placeholder: In the actual implementation, create a proper settings dialog

    def _open_database_viewer(self):
        """Open database viewer"""
        # This would open a new window to browse database records
        self._log_event("Database viewer opened")
        # Placeholder: In the actual implementation, create a database viewer window

    def _define_roi(self):
        """Define Region of Interest on the video frame with proper initialization"""
        if self.current_frame is None:
            messagebox.showerror("Error", "No video frame available. Load a video first.")
            return
        
        # Create a copy of the current frame for ROI selection
        self.roi_frame = self.current_frame.copy()
        self.roi_points = []
        
        # Create a new window for ROI selection
        roi_window = tk.Toplevel(self.root)
        roi_window.title("Define ROI")
        roi_window.geometry("800x600")
        
        # Create canvas for the image
        self.roi_canvas = tk.Canvas(roi_window, bg="black")
        self.roi_canvas.pack(fill=tk.BOTH, expand=True)
        
        # CRITICAL: Make sure the canvas is ready before binding events
        roi_window.update_idletasks()
        
        # Add instruction label
        instruction = ttk.Label(roi_window, 
                          text="Click to define points of ROI. Double-click to finish.")
        instruction.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Add buttons
        button_frame = ttk.Frame(roi_window)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(button_frame, text="Clear", command=self._clear_roi).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Done", command=lambda: self._finish_roi(roi_window)).pack(side=tk.RIGHT, padx=5)
        
        # Display the initial frame - do this before binding events
        self._display_roi_frame()
        
        # IMPORTANT: Wait for frame display to complete before binding
        roi_window.update()
        
        # Now bind mouse events AFTER canvas is created and updated
        self.roi_canvas.bind("<Button-1>", self._on_roi_click)
        self.roi_canvas.bind("<Double-Button-1>", lambda e: self._finish_roi(roi_window))
        
        # Save a reference to the ROI window
        self.roi_window = roi_window
    
    def _display_roi_frame(self):
        """Display the ROI frame on the canvas with proper scaling"""
        if not hasattr(self, 'roi_canvas') or not hasattr(self, 'roi_frame'):
            return
            
        # Get canvas dimensions after it's been mapped
        self.roi_canvas.update()
        canvas_width = self.roi_canvas.winfo_width() or 800
        canvas_height = self.roi_canvas.winfo_height() or 600
        
        # Convert frame to RGB for PIL
        frame_rgb = cv2.cvtColor(self.roi_frame, cv2.COLOR_BGR2RGB)
        
        # Create PIL image
        h, w = self.roi_frame.shape[:2]
        pil_img = Image.fromarray(frame_rgb)
        
        # Calculate ratio for resizing to fit canvas
        ratio = min(canvas_width / w, canvas_height / h)
        new_width = int(w * ratio)
        new_height = int(h * ratio)
        
        # Resize image
        pil_img = pil_img.resize((new_width, new_height), Image.LANCZOS)
        self.roi_photo = ImageTk.PhotoImage(image=pil_img)
        
        # Display centered image
        self.roi_canvas.create_image(
            canvas_width // 2, canvas_height // 2,
            image=self.roi_photo, 
            anchor=tk.CENTER
        )
        
        # Update coordinate manager with dimensions
        self.coord_manager.update_original_size(w, h)
        self.coord_manager.update_display_size(new_width, new_height)

    def _reset_roi(self):
        """Reset Region of Interest to default"""
        self._log_event("ROI reset to default")
        messagebox.showinfo("ROI Reset", "Region of Interest reset to default.")

    def _finish_roi(self, roi_window):
        """Finalize ROI selection"""
        if len(self.roi_points) < 3:
            messagebox.showerror("Error", "Please define at least 3 points for ROI")
            return
        
        # Use the points as-is without trying to sort or modify them
        # This preserves the exact polygon the user defined
        region = self.roi_points.copy()
        
        # Log the defined ROI
        self._log_event(f"ROI defined with {len(region)} points")
        
        # Set the ROI in the speed estimator
        if hasattr(self, 'on_roi_defined') and callable(self.on_roi_defined):
            self.on_roi_defined(region)
        
        # Close the ROI window
        roi_window.destroy()

    def _show_help(self):
        """Show help documentation"""
        help_text = """
        # Vehicle Speed Estimator - User Guide
        
        This application detects vehicles in videos and estimates their speed.
        
        ## Basic Usage:
        1. Click "Open Video" to select a video file
        2. Click "Start Processing" to begin detection
        3. View real-time statistics in the right panel
        
        ## Features:
        - Vehicle detection and tracking
        - Speed estimation
        - Database storage of vehicle information
        - AI-based vehicle details extraction
        """
        self._show_text_window("User Guide", help_text)

    def _show_about(self):
        """Show about information"""
        about_text = """
        # Vehicle Speed Estimator
        
        Version: 2.0
        Date: April 2, 2025
        
        A system for vehicle detection and speed estimation using 
        YOLOv5, OpenCV, and AI-powered analysis.
        
        Created by: LESLY B MUTANANGWA
        """
        self._show_text_window("About", about_text)


    def _on_roi_click(self, event):
        """Handle ROI click with proper coordinate transformation and error handling"""
        # Check if ROI canvas exists
        if not hasattr(self, 'roi_canvas') or self.roi_canvas is None:
            logger.error("ROI canvas not found in _on_roi_click")
            return
            
        # Check if ROI frame exists
        if not hasattr(self, 'roi_frame') or self.roi_frame is None:
            logger.error("ROI frame not found in _on_roi_click")
            return
        
        try:
            # Get canvas dimensions
            canvas_width = self.roi_canvas.winfo_width()
            canvas_height = self.roi_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                logger.warning(f"Invalid canvas dimensions: {canvas_width}x{canvas_height}")
                canvas_width = self.roi_canvas.winfo_reqwidth() 
                canvas_height = self.roi_canvas.winfo_reqheight()
            
            # Get original ROI frame dimensions
            h, w = self.roi_frame.shape[:2]
            
            # Calculate display ratio
            ratio = min(canvas_width / w, canvas_height / h)
            new_width = int(w * ratio)
            new_height = int(h * ratio)
            
            # Calculate offset if image is centered
            x_offset = (canvas_width - new_width) // 2
            y_offset = (canvas_height - new_height) // 2
            
            # Adjust event coordinates to account for centering
            rel_x = event.x - x_offset
            rel_y = event.y - y_offset
            
            # Check if click is inside the image area
            if rel_x < 0 or rel_y < 0 or rel_x >= new_width or rel_y >= new_height:
                logger.info(f"Click outside image area: ({event.x}, {event.y})")
                return
            
            # Convert back to original image coordinates
            orig_x = int(rel_x / ratio)
            orig_y = int(rel_y / ratio)
            
            logger.info(f"ROI Click: Canvas=({event.x}, {event.y}), Original=({orig_x}, {orig_y})")
            
            # Add point to ROI in ORIGINAL coordinates
            if not hasattr(self, 'roi_points'):
                self.roi_points = []
            
            self.roi_points.append((orig_x, orig_y))
            
            # Update the ROI display
            self._update_roi_display()
            
        except Exception as e:
            logger.exception(f"Error in ROI click handler: {e}")



    def _update_roi_display(self):
        """Update the ROI display with current points"""
        try:
            if not hasattr(self, 'roi_frame') or not hasattr(self, 'roi_canvas'):
                logger.error("Missing roi_frame or roi_canvas in _update_roi_display")
                return
                
            if self.roi_canvas.winfo_exists() == 0:
                logger.error("ROI canvas has been destroyed")
                return
                
            # Make a copy of the original frame
            roi_display = self.roi_frame.copy()
            
            # Draw all points and lines
            if hasattr(self, 'roi_points') and self.roi_points:
                # Draw points
                for point in self.roi_points:
                    cv2.circle(roi_display, point, 5, (0, 0, 255), -1)
                
                # Draw lines connecting the points
                if len(self.roi_points) > 1:
                    for i in range(len(self.roi_points) - 1):
                        cv2.line(
                            roi_display,
                            self.roi_points[i],
                            self.roi_points[i + 1],
                            (0, 255, 0),
                            2
                        )
                        
                    # Draw line connecting last point to first if we have at least 3 points
                    if len(self.roi_points) >= 3:
                        cv2.line(
                            roi_display,
                            self.roi_points[-1],
                            self.roi_points[0],
                            (0, 255, 0),
                            2
                        )
            
            # Convert to RGB for display
            rgb_display = cv2.cvtColor(roi_display, cv2.COLOR_BGR2RGB)
            
            # Get canvas dimensions
            canvas_width = self.roi_canvas.winfo_width()
            canvas_height = self.roi_canvas.winfo_height()
            
            # Use minimum size if not yet properly sized
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 800
                canvas_height = 600
            
            # Get original dimensions
            h, w = roi_display.shape[:2]
            
            # Calculate ratio for resizing
            ratio = min(canvas_width / w, canvas_height / h)
            new_width = int(w * ratio)
            new_height = int(h * ratio)
            
            # Resize image
            pil_img = Image.fromarray(rgb_display).resize((new_width, new_height), Image.LANCZOS)
            self.roi_photo = ImageTk.PhotoImage(image=pil_img)
            
            # Clear canvas and display centered image
            self.roi_canvas.delete("all")
            
            # Calculate center position
            x_pos = canvas_width // 2
            y_pos = canvas_height // 2
            
            self.roi_canvas.create_image(
                x_pos, y_pos,
                image=self.roi_photo,
                anchor=tk.CENTER
            )
        except Exception as e:
            logger.exception(f"Error updating ROI display: {e}")

    def _clear_roi(self):
        """Clear ROI selection"""
        self.roi_points = []
        self._log_event("ROI selection cleared")
        
        # Update the ROI display
        if hasattr(self, 'roi_frame') and hasattr(self, 'roi_canvas'):
            self._update_roi_display()
        
    def _show_text_window(self, title: str, content: str):
        """Show a window with scrollable text content"""
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("500x400")
        window.transient(self.root)  # Make the window transient to the main window
        
        text_widget = tk.Text(window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(window, command=text_widget.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        text_widget.config(yscrollcommand=scrollbar.set)
        
        text_widget.insert(tk.END, content)
        text_widget.config(state=tk.DISABLED)  # Make it read-only
        
        ttk.Button(window, text="Close", command=window.destroy).pack(pady=10)