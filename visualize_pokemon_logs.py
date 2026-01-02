import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path
import numpy as np
from collections import defaultdict
from datetime import datetime

class PokemonMovementVisualizer:
    def __init__(self, base_folder="Logging"):
        self.base_folder = Path(base_folder)
        self.day_folders = []
    
    # Find all day-specific folders (pokemon_log_YYYYMMDD)
    def find_day_folders(self):
        self.day_folders = sorted([d for d in self.base_folder.iterdir() 
                                   if d.is_dir() and d.name.startswith("pokemon_log_")])
        
        if not self.day_folders:
            print(f"No day folders found in {self.base_folder}")
            return False
        
        print(f"Found {len(self.day_folders)} day folders:")
        for folder in self.day_folders:
            print(f"  - {folder.name}")
        return True
    
    # Load all CSV files from a specific day folder
    def load_day_logs(self, day_folder):
        csv_files = sorted(day_folder.glob("*.csv"))
        
        if not csv_files:
            print(f"  No CSV files found in {day_folder.name}")
            return None
        
        print(f"  Loading {len(csv_files)} CSV files from {day_folder.name}")
        
        all_data = []
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                df['source_file'] = csv_file.name
                all_data.append(df)
            except Exception as e:
                print(f"  Error loading {csv_file.name}: {e}")
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            print(f"  Total entries for {day_folder.name}: {len(combined_df)}")
            return combined_df
        return None
    
    # Group data by map bank and number
    def get_map_groups(self, df):
        map_groups = defaultdict(list)
        
        for _, row in df.iterrows():
            map_key = (row['mapBank'], row['mapNum'])
            map_groups[map_key].append(row)
        
        return map_groups
    
    # Visualize movement on a single map
    def visualize_map(self, map_bank, map_num, data, ax=None):
        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 10))
        
        # Extract coordinates
        x_coords = [row['x'] for row in data]
        y_coords = [row['y'] for row in data]
        
        # Create a grid background
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        # Add padding
        padding = 2
        min_x -= padding
        max_x += padding
        min_y -= padding
        max_y += padding
        
        # Draw grid
        for x in range(int(min_x), int(max_x) + 1):
            ax.axvline(x, color='lightgray', linewidth=0.5, alpha=0.3)
        for y in range(int(min_y), int(max_y) + 1):
            ax.axhline(y, color='lightgray', linewidth=0.5, alpha=0.3)
        
        # Plot path with gradient color (blue to red = start to end)
        colors = plt.cm.viridis(np.linspace(0, 1, len(x_coords)))
        
        for i in range(len(x_coords) - 1):
            ax.plot([x_coords[i], x_coords[i+1]], 
                   [y_coords[i], y_coords[i+1]], 
                   color=colors[i], linewidth=2, alpha=0.6)
        
        # Mark start and end positions
        ax.scatter(x_coords[0], y_coords[0], 
                  color='green', s=200, marker='o', 
                  label='Start', zorder=5, edgecolors='black', linewidths=2)
        ax.scatter(x_coords[-1], y_coords[-1], 
                  color='red', s=200, marker='X', 
                  label='End', zorder=5, edgecolors='black', linewidths=2)
        
        # Create heatmap of visited positions
        position_counts = defaultdict(int)
        for x, y in zip(x_coords, y_coords):
            position_counts[(x, y)] += 1
        
        # Draw heatmap squares
        max_visits = max(position_counts.values())
        for (x, y), count in position_counts.items():
            intensity = count / max_visits
            rect = patches.Rectangle((x - 0.4, y - 0.4), 0.8, 0.8,
                                    linewidth=1, edgecolor='none',
                                    facecolor='yellow', alpha=intensity * 0.5)
            ax.add_patch(rect)
        
        ax.set_xlim(min_x - 0.5, max_x + 0.5)
        ax.set_ylim(min_y - 0.5, max_y + 0.5)
        ax.set_aspect('equal')
        ax.invert_yaxis()  # Invert Y axis to match game coordinates
        
        # Remove decimal labels from axes
        ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
        ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
        
        # Map name
        map_name = self.get_map_name(map_bank, map_num)
        ax.set_title(f'{map_name}\n{len(data)} steps', fontsize=14, fontweight='bold')
        ax.set_xlabel('X Coordinate')
        ax.set_ylabel('Y Coordinate')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        
        return ax
    
    # Get human-readable map name (add more as needed)
    def get_map_name(self, bank, num):
        # Bank 0 is typically overworld routes
        if bank == 0:
            return f"Overworld - Map {num}"
        return f"Bank {bank} - Map {num}"
    
    # Create a summary visualization of all maps for a specific day
    def create_summary_visualization(self, df, output_file):
        map_groups = self.get_map_groups(df)
        num_maps = len(map_groups)
        
        if num_maps == 0:
            print("No map data to visualize")
            return
        
        # Calculate grid size
        cols = min(3, num_maps)
        rows = (num_maps + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(6*cols, 5*rows))
        if num_maps == 1:
            axes = [axes]
        else:
            axes = axes.flatten() if num_maps > 1 else [axes]
        
        # Plot each map
        for idx, ((map_bank, map_num), data) in enumerate(sorted(map_groups.items())):
            self.visualize_map(map_bank, map_num, data, axes[idx])
        
        # Hide unused subplots
        for idx in range(num_maps, len(axes)):
            axes[idx].axis('off')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"  Saved summary visualization to {output_file}")
        plt.close()
    
    # Create individual visualizations for each map for a specific day
    def create_individual_maps(self, df, output_folder):
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
        
        map_groups = self.get_map_groups(df)
        
        for (map_bank, map_num), data in sorted(map_groups.items()):
            fig, ax = plt.subplots(figsize=(12, 10))
            self.visualize_map(map_bank, map_num, data, ax)
            
            filename = f"map_bank{map_bank}_num{map_num}.png"
            filepath = output_path / filename
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()
            print(f"  Saved {filename}")
    
    # Print summary statistics for a specific day
    def print_statistics(self, df, day_name):
        print("\n" + "="*50)
        print(f"MOVEMENT STATISTICS - {day_name}")
        print("="*50)
        
        map_groups = self.get_map_groups(df)
        
        for (map_bank, map_num), data in sorted(map_groups.items()):
            map_name = self.get_map_name(map_bank, map_num)
            print(f"\n{map_name}:")
            print(f"  Total steps: {len(data)}")
            
            x_coords = [row['x'] for row in data]
            y_coords = [row['y'] for row in data]
            print(f"  X range: {min(x_coords)} to {max(x_coords)}")
            print(f"  Y range: {min(y_coords)} to {max(y_coords)}")
            
            # Count unique positions
            unique_positions = len(set(zip(x_coords, y_coords)))
            print(f"  Unique positions visited: {unique_positions}")
    
    # Process all day folders
    def process_all_days(self):
        if not self.find_day_folders():
            return
        
        for day_folder in self.day_folders:
            print(f"\n{'='*50}")
            print(f"Processing {day_folder.name}")
            print(f"{'='*50}")
            
            # Load logs for this day
            df = self.load_day_logs(day_folder)
            if df is None:
                continue
            
            # Create output folder for this day
            output_folder = Path("Map_Visualizations") / day_folder.name
            output_folder.mkdir(parents=True, exist_ok=True)
            
            # Print statistics
            self.print_statistics(df, day_folder.name)
            
            # Create summary visualization
            summary_path = output_folder / "movement_summary.png"
            self.create_summary_visualization(df, summary_path)
            
            # Create individual map visualizations
            self.create_individual_maps(df, output_folder)
        
        print("\n" + "="*50)
        print("All visualizations complete!")
        print("="*50)


# Main execution
if __name__ == "__main__":
    # Initialize visualizer
    visualizer = PokemonMovementVisualizer(base_folder="Logging")
    
    # Process all day folders
    visualizer.process_all_days()