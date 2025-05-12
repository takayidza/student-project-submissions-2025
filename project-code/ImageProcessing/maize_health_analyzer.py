import cv2
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import pandas as pd
import os
from datetime import datetime

class MaizeHealthAnalyzerImproved:
    """
    An improved class for analyzing maize crop health using enhanced classical image processing.
    """

    def __init__(self):
        # Refined color ranges for healthy maize (in HSV)
        self.healthy_green_lower = np.array([30, 40, 40])
        self.healthy_green_upper = np.array([90, 255, 255])

        # More specific nutrient deficiency color indicators (in HSV) - Still needs careful tuning
        self.nutrient_indicators = {
            'nitrogen': {'lower': np.array([20, 100, 100]), 'upper': np.array([40, 255, 255])},  # Yellowing
            'phosphorus': {'lower': np.array([130, 50, 50]), 'upper': np.array([180, 255, 255])},  # Purplish
            'potassium': {'lower': np.array([20, 80, 80]), 'upper': np.array([40, 255, 255])},  # Yellow edges/tips
            'magnesium': {'lower': np.array([20, 50, 50]), 'upper': np.array([40, 255, 255])},  # Interveinal yellowing
            'sulfur': {'lower': np.array([20, 100, 100]), 'upper': np.array([40, 255, 255])},  # Uniform yellowing
            'calcium': {'lower': np.array([20, 50, 50]), 'upper': np.array([40, 255, 255])}   # Pale green/yellow new leaves
        }

        self.results = {
            'sampleId': None,
            'sampleDate': None,
            'nitrogenScore': 0,
            'phosphorusScore': 0,
            'potassiumScore': 0,
            'magnesiumScore': 0,
            'sulfurScore': 0,
            'calciumScore': 0,
            'wiltingScore': 0,
            'damageDetected': False,
            'damageSeverity': 'None',
            'dominantColors': [],
            'healthStatus': None,
            'objectsDetectedCount': 0 # For counting damage instances
        }

    def load_image(self, image_path):
        """Load an image from the given path."""
        self.original_image = cv2.imread(image_path)
        if self.original_image is None:
            raise ValueError(f"Could not load image from {image_path}")

        self.image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
        self.hsv_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2HSV)
        self.lab_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2LAB) # For potential color normalization

        # Generate a sample ID if none exists
        self.results['sampleId'] = os.path.basename(image_path).split('.')[0]
        self.results['sampleDate'] = datetime.now().strftime("%Y-%m-%d")

        return self.image

    def segment_plant(self):
        """More robust plant segmentation using color information."""
        lower_green = np.array([20, 30, 30])
        upper_green = np.array([100, 255, 255])
        mask = cv2.inRange(cv2.cvtColor(self.original_image, cv2.COLOR_BGR2HSV), lower_green, upper_green)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        self.plant_mask = mask
        self.segmented = cv2.bitwise_and(self.original_image, self.original_image, mask=self.plant_mask)
        self.masked_hsv = cv2.bitwise_and(self.hsv_image, self.hsv_image, mask=self.plant_mask)
        self.masked_lab = cv2.bitwise_and(self.lab_image, self.lab_image, mask=self.plant_mask)
        self.masked_gray = cv2.cvtColor(self.segmented, cv2.COLOR_RGB2GRAY)
        return self.segmented

    def analyze_colors(self):
        """Analyze colors in the masked image."""
        plant_pixels = self.masked_hsv[self.plant_mask > 0].reshape(-1, 3)

        if plant_pixels.size > 0:
            kmeans = KMeans(n_clusters=5, n_init=10)
            kmeans.fit(plant_pixels)
            colors = kmeans.cluster_centers_
            labels = kmeans.labels_
            counts = np.bincount(labels)
            self.results['dominantColors'] = [color.astype(int).tolist() for color in colors]

            total_plant_pixels = plant_pixels.shape[0]
            green_mask_plant = cv2.inRange(self.masked_hsv, self.healthy_green_lower, self.healthy_green_upper)
            green_pixels = cv2.countNonZero(green_mask_plant)
            green_percentage = (green_pixels / total_plant_pixels) * 100 if total_plant_pixels > 0 else 0

            for nutrient, ranges in self.nutrient_indicators.items():
                deficiency_mask_plant = cv2.inRange(self.masked_hsv, ranges['lower'], ranges['upper'])
                deficiency_pixels = cv2.countNonZero(deficiency_mask_plant)
                deficiency_percentage = (deficiency_pixels / total_plant_pixels) * 100 if total_plant_pixels > 0 else 0
                score = max(1, min(10, int(10 - (deficiency_percentage / 3))))  # Adjusted scoring
                self.results[f'{nutrient}Score'] = score

            if green_percentage > 80:
                self.results['healthStatus'] = "Excellent"
            elif green_percentage > 65:
                self.results['healthStatus'] = "Good"
            elif green_percentage > 40:
                self.results['healthStatus'] = "Fair"
            else:
                self.results['healthStatus'] = "Poor"
        else:
            self.results['healthStatus'] = "Insufficient Plant Pixels"
            for nutrient in self.nutrient_indicators:
                self.results[f'{nutrient}Score'] = 5  # Default score

        return self.results

    def detect_wilting(self):
        """Detect wilting using edge detection on the segmented plant."""
        edges = cv2.Canny(self.masked_gray, 30, 100)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            total_perimeter = sum(cv2.arcLength(cnt, True) for cnt in contours)
            plant_area = cv2.countNonZero(self.plant_mask)
            if plant_area > 0 and total_perimeter > 0:
                perimeter_to_area_ratio = total_perimeter / plant_area
                wilting_score = max(1, min(10, int(10 - (perimeter_to_area_ratio * 100)))) # Adjusted scoring
                self.results['wiltingScore'] = wilting_score
            else:
                self.results['wiltingScore'] = 9
        else:
            self.results['wiltingScore'] = 10

        return self.results

    def detect_damage(self):
        """Detect potential leaf damage by finding non-green regions within the plant mask."""
        non_green_mask = cv2.bitwise_not(cv2.inRange(self.masked_hsv, self.healthy_green_lower, self.healthy_green_upper))
        damage_mask = cv2.bitwise_and(non_green_mask, self.plant_mask)
        kernel = np.ones((3, 3), np.uint8)
        damage_mask = cv2.morphologyEx(damage_mask, cv2.MORPH_OPEN, kernel, iterations=2)
        damage_contours, _ = cv2.findContours(damage_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        significant_damage_count = 0
        total_damage_area = 0
        damage_area_threshold = 20  # Minimum area for damage

        for contour in damage_contours:
            area = cv2.contourArea(contour)
            if area > damage_area_threshold:
                significant_damage_count += 1
                total_damage_area += area

        self.results['damageDetected'] = significant_damage_count > 0
        self.results['objectsDetectedCount'] = significant_damage_count

        if significant_damage_count > 5 or total_damage_area > 500:
            self.results['damageSeverity'] = 'High'
        elif significant_damage_count > 2 or total_damage_area > 200:
            self.results['damageSeverity'] = 'Medium'
        elif significant_damage_count > 0:
            self.results['damageSeverity'] = 'Low'
        else:
            self.results['damageSeverity'] = 'None'

        return self.results

    def analyze_image(self, image_path):
        """Perform a complete analysis of the image."""
        try:
            self.load_image(image_path)
            self.segment_plant()
            self.analyze_colors()
            self.detect_wilting()
            self.detect_damage()
            return self.results
        except Exception as e:
            print(f"Error during analysis: {e}")
            return self.results

    def visualize_results(self, save_path=None):
        """Visualize the analysis results."""
        fig, axs = plt.subplots(2, 2, figsize=(15, 10))

        axs[0, 0].imshow(self.image)
        axs[0, 0].set_title('Original Image')
        axs[0, 0].axis('off')

        axs[0, 1].imshow(cv2.cvtColor(self.segmented, cv2.COLOR_BGR2RGB))
        axs[0, 1].set_title('Segmented Plant')
        axs[0, 1].axis('off')

        edges_wilting = cv2.Canny(self.masked_gray, 30, 100)
        axs[1, 0].imshow(edges_wilting, cmap='gray')
        axs[1, 0].set_title(f'Wilting Edges (Score: {self.results["wiltingScore"]:.2f})')
        axs[1, 0].axis('off')

        nutrients_labels = ['Nitrogen', 'Phosphorus', 'Potassium', 'Magnesium', 'Sulfur', 'Calcium']
        nutrient_keys = ['nitrogenScore', 'phosphorusScore', 'potassiumScore', 'magnesiumScore', 'sulfurScore', 'calciumScore']
        scores = [self.results[key] for key in nutrient_keys]
        axs[1, 1].bar(nutrients_labels, scores, color='skyblue')
        axs[1, 1].set_title('Nutrient Scores (Higher is Better)')
        axs[1, 1].set_ylim(0, 10)
        axs[1, 1].set_ylabel('Score')
        plt.xticks(rotation=45, ha='right')

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path)
            plt.close()
        else:
            plt.show()
            
    def save_results_to_csv(self, output_path):
        """Save the analysis results to a CSV file."""
        df = pd.DataFrame([self.results])
        df.to_csv(output_path, index=False)
        print(f"Results saved to {output_path}")
