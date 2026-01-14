import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

class RewardAnalyzer:
    def __init__(self, base_folder="Logging"):
        self.base_folder = Path(base_folder)
        self.day_folders = []
        self.max_steps = 1000
    
    def find_day_folders(self):
        """Find all day-specific folders (pokemon_log_YYYYMMDD)"""
        self.day_folders = sorted([d for d in self.base_folder.iterdir() 
                                   if d.is_dir() and d.name.startswith("pokemon_log_")])
        
        if not self.day_folders:
            print(f"No day folders found in {self.base_folder}")
            return False
        
        print(f"Found {len(self.day_folders)} day folders:")
        for folder in self.day_folders:
            print(f"  - {folder.name}")
        return True
    
    def load_day_logs(self, day_folder):
        """Load all CSV files from a specific day folder"""
        csv_files = sorted(day_folder.glob("*.csv"))
        
        if not csv_files:
            print(f"  No CSV files found in {day_folder.name}")
            return []
        
        print(f"  Loading {len(csv_files)} CSV files from {day_folder.name}")
        
        all_runs = []
        runs_with_rewards = 0
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                
                # Check if reward column exists
                if 'reward' not in df.columns:
                    print(f"  Warning: {csv_file.name} has no 'reward' column - skipping")
                    continue
                
                # Check if there are any non-zero rewards
                if df['reward'].notna().any():
                    df['source_file'] = csv_file.name
                    all_runs.append(df)
                    runs_with_rewards += 1
                else:
                    print(f"  Warning: {csv_file.name} has only NaN/empty rewards - skipping")
                    
            except Exception as e:
                print(f"  Error loading {csv_file.name}: {e}")
        
        print(f"  Loaded {runs_with_rewards} runs with valid reward data")
        return all_runs
    
    def extract_reward_trajectory(self, df):
        """Extract step-reward pairs from a single run"""
        # Filter out rows where currentSteps might be missing
        df = df[df['currentSteps'].notna()].copy()
        
        if len(df) == 0:
            return None
        
        # Get step and reward data
        steps = df['currentSteps'].values
        rewards = df['reward'].values
        
        return {'steps': steps, 'rewards': rewards}
    
    def compute_average_reward_curve(self, runs_data):
        """Compute average reward across all runs at each step"""
        # Create a dictionary to store rewards at each step
        step_rewards = defaultdict(list)
        
        for run in runs_data:
            trajectory = self.extract_reward_trajectory(run)
            if trajectory is None:
                continue
            
            for step, reward in zip(trajectory['steps'], trajectory['rewards']):
                step_rewards[int(step)].append(reward)
        
        # Compute average and std for each step
        steps = sorted(step_rewards.keys())
        avg_rewards = []
        std_rewards = []
        counts = []
        
        for step in steps:
            rewards_at_step = step_rewards[step]
            avg_rewards.append(np.mean(rewards_at_step))
            std_rewards.append(np.std(rewards_at_step))
            counts.append(len(rewards_at_step))
        
        return {
            'steps': np.array(steps),
            'avg_rewards': np.array(avg_rewards),
            'std_rewards': np.array(std_rewards),
            'counts': np.array(counts)
        }
    
    def plot_average_reward(self, curve_data, output_file, day_name):
        """Create a plot of average reward vs steps"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        steps = curve_data['steps']
        avg_rewards = curve_data['avg_rewards']
        std_rewards = curve_data['std_rewards']
        counts = curve_data['counts']
        
        # Plot 1: Average reward with standard deviation
        ax1.plot(steps, avg_rewards, 'b-', linewidth=2, label='Average Reward')
        ax1.fill_between(steps, 
                         avg_rewards - std_rewards, 
                         avg_rewards + std_rewards,
                         alpha=0.3, color='blue', label='±1 Std Dev')
        
        ax1.set_xlabel('Steps', fontsize=12)
        ax1.set_ylabel('Average Reward', fontsize=12)
        ax1.set_title(f'Average Reward vs Steps - {day_name}', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='best')
        
        # Add max steps reference line
        if max(steps) < self.max_steps:
            ax1.axvline(x=self.max_steps, color='r', linestyle='--', 
                       alpha=0.5, label=f'Max Steps ({self.max_steps})')
        
        # Plot 2: Number of runs at each step
        ax2.plot(steps, counts, 'g-', linewidth=2)
        ax2.fill_between(steps, counts, alpha=0.3, color='green')
        ax2.set_xlabel('Steps', fontsize=12)
        ax2.set_ylabel('Number of Runs', fontsize=12)
        ax2.set_title('Number of Active Runs at Each Step', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"  Saved reward plot to {output_file}")
        plt.close()
    
    def plot_individual_runs(self, runs_data, output_file, day_name, max_runs=20):
        """Plot individual run trajectories (limited to max_runs for clarity)"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        num_runs = min(len(runs_data), max_runs)
        colors = plt.cm.tab20(np.linspace(0, 1, num_runs))
        
        for idx, run in enumerate(runs_data[:num_runs]):
            trajectory = self.extract_reward_trajectory(run)
            if trajectory is None:
                continue
            
            source_file = run['source_file'].iloc[0] if 'source_file' in run.columns else f'Run {idx+1}'
            ax.plot(trajectory['steps'], trajectory['rewards'], 
                   color=colors[idx], alpha=0.6, linewidth=1.5,
                   label=source_file if num_runs <= 10 else None)
        
        ax.set_xlabel('Steps', fontsize=12)
        ax.set_ylabel('Reward', fontsize=12)
        ax.set_title(f'Individual Run Trajectories - {day_name}\n(Showing {num_runs}/{len(runs_data)} runs)', 
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        if num_runs <= 10:
            ax.legend(loc='best', fontsize=8)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"  Saved individual runs plot to {output_file}")
        plt.close()
    
    def print_statistics(self, runs_data, curve_data, day_name):
        """Print summary statistics"""
        print("\n" + "="*60)
        print(f"REWARD STATISTICS - {day_name}")
        print("="*60)
        
        print(f"\nTotal runs analyzed: {len(runs_data)}")
        
        # Overall statistics
        all_final_rewards = []
        all_max_steps = []
        
        for run in runs_data:
            trajectory = self.extract_reward_trajectory(run)
            if trajectory is None:
                continue
            all_final_rewards.append(trajectory['rewards'][-1])
            all_max_steps.append(trajectory['steps'][-1])
        
        if all_final_rewards:
            print(f"\nFinal Reward Statistics:")
            print(f"  Mean: {np.mean(all_final_rewards):.4f}")
            print(f"  Std:  {np.std(all_final_rewards):.4f}")
            print(f"  Min:  {np.min(all_final_rewards):.4f}")
            print(f"  Max:  {np.max(all_final_rewards):.4f}")
        
        if all_max_steps:
            print(f"\nSteps Reached:")
            print(f"  Mean: {np.mean(all_max_steps):.2f}")
            print(f"  Std:  {np.std(all_max_steps):.2f}")
            print(f"  Min:  {int(np.min(all_max_steps))}")
            print(f"  Max:  {int(np.max(all_max_steps))}")
            runs_to_max = sum(1 for s in all_max_steps if s >= self.max_steps)
            print(f"  Runs reaching {self.max_steps} steps: {runs_to_max}/{len(all_max_steps)}")
        
        # Step-wise statistics
        if curve_data['steps'].size > 0:
            print(f"\nStep-wise Average Reward:")
            print(f"  Initial (step 0): {curve_data['avg_rewards'][0]:.4f}")
            print(f"  Final (step {int(curve_data['steps'][-1])}): {curve_data['avg_rewards'][-1]:.4f}")
            print(f"  Maximum: {np.max(curve_data['avg_rewards']):.4f} at step {int(curve_data['steps'][np.argmax(curve_data['avg_rewards'])])}")
    
    def process_all_days(self):
        """Process all day folders"""
        if not self.find_day_folders():
            return
        
        for day_folder in self.day_folders:
            print(f"\n{'='*60}")
            print(f"Processing {day_folder.name}")
            print(f"{'='*60}")
            
            # Load logs for this day
            runs_data = self.load_day_logs(day_folder)
            if not runs_data:
                print(f"  No valid runs found for {day_folder.name}")
                continue
            
            # Create output folder
            output_folder = Path("Results_Runs") / day_folder.name
            output_folder.mkdir(parents=True, exist_ok=True)
            
            # Compute average reward curve
            curve_data = self.compute_average_reward_curve(runs_data)
            
            if curve_data['steps'].size == 0:
                print(f"  No valid reward data to plot")
                continue
            
            # Print statistics
            self.print_statistics(runs_data, curve_data, day_folder.name)
            
            # Create visualizations
            avg_reward_path = output_folder / "average_reward_vs_steps.png"
            self.plot_average_reward(curve_data, avg_reward_path, day_folder.name)
            
            individual_runs_path = output_folder / "individual_runs.png"
            self.plot_individual_runs(runs_data, individual_runs_path, day_folder.name)
        
        print("\n" + "="*60)
        print("All reward analysis complete!")
        print(f"Results saved in: Results_Runs/")
        print("="*60)


# Main execution
if __name__ == "__main__":
    # Initialize analyzer
    analyzer = RewardAnalyzer(base_folder="Logging")
    
    # Process all day folders
    analyzer.process_all_days()