import os
import sys
from maize_health_analyzer import MaizeHealthAnalyzer
import matplotlib.pyplot as plt
import pandas as pd

def analyze_multiple_images(image_folder, output_folder):
    """
    Analyze all images in a folder and generate reports
    
    Args:
        image_folder (str): Path to folder containing maize images
        output_folder (str): Path to save analysis results
    """
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Initialize analyzer
    analyzer = MaizeHealthAnalyzer()
    
    # Get all image files
    image_files = [f for f in os.listdir(image_folder) 
                  if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    all_results = []
    
    for image_file in image_files:
        image_path = os.path.join(image_folder, image_file)
        sample_id = os.path.splitext(image_file)[0]
        
        print(f"Analyzing image: {image_file}")
        
        # Analyze image
        results = analyzer.analyze_image(image_path)
        all_results.append(results)
        
        # Save visualization
        vis_output = os.path.join(output_folder, f"{sample_id}_analysis.png")
        analyzer.visualize_results(vis_output)
        
    # Combine all results and save to CSV
    if all_results:
        df = pd.DataFrame(all_results)
        csv_path = os.path.join(output_folder, "all_results.csv")
        df.to_csv(csv_path, index=False)
        print(f"All results saved to {csv_path}")
        
        # Generate summary statistics
        generate_summary_report(df, output_folder)

def generate_summary_report(df, output_folder):
    """Generate summary statistics and plots from all results"""
    # Create a summary report
    summary = {
        'total_samples': len(df),
        'avg_nitrogen_score': df['nitrogenScore'].mean(),
        'avg_phosphorus_score': df['phosphorusScore'].mean(),
        'avg_potassium_score': df['potassiumScore'].mean(),
        'avg_magnesium_score': df['magnesiumScore'].mean(),
        'avg_sulfur_score': df['sulfurScore'].mean(),
        'avg_calcium_score': df['calciumScore'].mean(),
        'avg_wilting_score': df['wiltingScore'].mean(),
        'damage_detected_percent': (df['damageDetected'].sum() / len(df)) * 100
    }
    
    # Save summary to text file
    with open(os.path.join(output_folder, "summary_report.txt"), 'w') as f:
        f.write("MAIZE CROP HEALTH ANALYSIS SUMMARY\n")
        f.write("==================================\n\n")
        f.write(f"Total samples analyzed: {summary['total_samples']}\n\n")
        f.write("AVERAGE NUTRIENT SCORES (1-10, higher is better):\n")
        f.write(f"  Nitrogen: {summary['avg_nitrogen_score']:.2f}\n")
        f.write(f"  Phosphorus: {summary['avg_phosphorus_score']:.2f}\n")
        f.write(f"  Potassium: {summary['avg_potassium_score']:.2f}\n")
        f.write(f"  Magnesium: {summary['avg_magnesium_score']:.2f}\n")
        f.write(f"  Sulfur: {summary['avg_sulfur_score']:.2f}\n")
        f.write(f"  Calcium: {summary['avg_calcium_score']:.2f}\n\n")
        f.write(f"Average Wilting Score: {summary['avg_wilting_score']:.2f}\n")
        f.write(f"Percentage of samples with damage detected: {summary['damage_detected_percent']:.2f}%\n")
    
    # Generate summary charts
    plt.figure(figsize=(12, 8))
    
    # Nutrient scores chart
    nutrients = ['Nitrogen', 'Phosphorus', 'Potassium', 'Magnesium', 'Sulfur', 'Calcium']
    avg_scores = [summary[f'avg_{n.lower()}_score'] for n in nutrients]
    
    plt.bar(nutrients, avg_scores, color='green')
    plt.axhline(y=7, color='r', linestyle='--', label='Recommended minimum score')
    plt.title('Average Nutrient Scores Across All Samples')
    plt.ylabel('Score (1-10)')
    plt.ylim(0, 10)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    plt.savefig(os.path.join(output_folder, "nutrient_summary.png"))
    print(f"Summary report generated in {output_folder}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python example_usage.py <image_folder> <output_folder>")
        sys.exit(1)
    
    image_folder = sys.argv[1]
    output_folder = sys.argv[2]
    
    analyze_multiple_images(image_folder, output_folder)