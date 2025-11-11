#!/usr/bin/env python3
"""
Workpiece Visualization Script
Visualizes a workpiece contour and its spray patterns from JSON data.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def extract_points(contour_data):
    """Extract x,y coordinates from nested contour structure."""
    points = []
    for point in contour_data:
        # Handle nested structure like [[[x, y]]]
        while isinstance(point, list) and len(point) == 1:
            point = point[0]
        if len(point) >= 2:
            points.append([float(point[0]), float(point[1])])
    return np.array(points)

def visualize_workpiece(json_path):
    """Load and visualize workpiece from JSON file."""
    
    # Load JSON data
    with open(json_path, 'r') as f:
        workpiece = json.load(f)
    
    # Extract main information
    workpiece_id = workpiece.get('workpieceId', 'Unknown')
    name = workpiece.get('name', 'Unnamed')
    glue_type = workpiece.get('glueType', 'Unknown')
    height = workpiece.get('height', 0)
    area = workpiece.get('contourArea', 0)
    
    # Create figure with subplots
    fig = plt.figure(figsize=(16, 10))
    
    # Main plot
    ax_main = plt.subplot(2, 2, (1, 2))
    
    # Extract and plot main contour
    main_contour = workpiece['contour']['contour']
    main_points = extract_points(main_contour)
    
    # Plot main contour (outer boundary)
    ax_main.plot(main_points[:, 0], main_points[:, 1], 'b-', linewidth=3, 
                label=f'Main Contour (Area: {area:.1f})', marker='o', markersize=4)
    
    # Fill the main contour with light blue
    ax_main.fill(main_points[:, 0], main_points[:, 1], 'lightblue', alpha=0.3)
    
    # Extract and plot spray patterns
    spray_patterns = workpiece.get('sprayPattern', {}).get('Contour', [])
    colors = ['red', 'green', 'orange', 'purple', 'brown']
    
    for i, pattern in enumerate(spray_patterns):
        if pattern.get('contour') and len(pattern['contour']) > 0:
            spray_points = extract_points(pattern['contour'])
            color = colors[i % len(colors)]
            
            # Plot spray pattern as thick line
            ax_main.plot(spray_points[:, 0], spray_points[:, 1], 
                        color=color, linewidth=4, alpha=0.8,
                        label=f'Spray Pattern {i+1}', marker='s', markersize=6)
            
            # Add arrows to show spray direction
            if len(spray_points) >= 2:
                for j in range(len(spray_points) - 1):
                    start = spray_points[j]
                    end = spray_points[j + 1]
                    dx = end[0] - start[0]
                    dy = end[1] - start[1]
                    ax_main.arrow(start[0], start[1], dx*0.7, dy*0.7, 
                                head_width=8, head_length=10, fc=color, ec=color, alpha=0.6)
    
    # Set main plot properties
    ax_main.set_xlabel('X Coordinate (pixels)', fontsize=12)
    ax_main.set_ylabel('Y Coordinate (pixels)', fontsize=12)
    ax_main.set_title(f'Workpiece Visualization\nID: {workpiece_id} | Name: "{name}" | Type: {glue_type}', 
                     fontsize=14, fontweight='bold')
    ax_main.grid(True, alpha=0.3)
    ax_main.legend(loc='best')
    ax_main.set_aspect('equal')
    
    # Invert Y-axis to match image coordinates
    ax_main.invert_yaxis()
    
    # Add point numbers to main contour
    for i, point in enumerate(main_points[:-1]):  # Skip last point if it's duplicate
        ax_main.annotate(f'{i}', (point[0], point[1]), xytext=(5, 5), 
                        textcoords='offset points', fontsize=8, 
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    # Detailed view subplot
    ax_detail = plt.subplot(2, 2, 3)
    
    # Plot just the spray patterns for detail
    for i, pattern in enumerate(spray_patterns):
        if pattern.get('contour') and len(pattern['contour']) > 0:
            spray_points = extract_points(pattern['contour'])
            color = colors[i % len(colors)]
            
            ax_detail.plot(spray_points[:, 0], spray_points[:, 1], 
                          color=color, linewidth=3, marker='o', markersize=8,
                          label=f'Pattern {i+1}: {len(spray_points)} points')
            
            # Add point coordinates as text
            for j, point in enumerate(spray_points):
                ax_detail.annotate(f'P{j}\n({point[0]:.1f},{point[1]:.1f})', 
                                 (point[0], point[1]), xytext=(10, 10),
                                 textcoords='offset points', fontsize=8,
                                 bbox=dict(boxstyle='round,pad=0.3', 
                                         facecolor=color, alpha=0.3))
    
    ax_detail.set_title('Spray Patterns Detail', fontsize=12, fontweight='bold')
    ax_detail.grid(True, alpha=0.3)
    ax_detail.legend()
    ax_detail.set_aspect('equal')
    ax_detail.invert_yaxis()
    
    # Information panel
    ax_info = plt.subplot(2, 2, 4)
    ax_info.axis('off')
    
    # Compile workpiece information
    info_text = f"""
WORKPIECE INFORMATION
═══════════════════════

ID: {workpiece_id}
Name: {name if name else 'Unnamed'}
Description: {workpiece.get('description', 'None')}

GEOMETRY
─────────────────
• Area: {area:.1f} sq pixels
• Height: {height} mm
• Points in main contour: {len(main_points)}

SPRAY CONFIGURATION
─────────────────────
• Glue Type: {glue_type}
• Spray Width: {workpiece.get('spray_width', 'N/A')} mm
• Program: {workpiece.get('program', 'N/A')}
• Material: {workpiece.get('material', 'N/A')}

SPRAY PATTERNS
──────────────
• Total patterns: {len(spray_patterns)}
"""
    
    # Add spray pattern details
    for i, pattern in enumerate(spray_patterns):
        if pattern.get('contour') and len(pattern['contour']) > 0:
            spray_points = extract_points(pattern['contour'])
            settings = pattern.get('settings', {})
            spray_height = settings.get('Spraying Height', 'N/A')
            fan_speed = settings.get('Fan Speed', 'N/A')
            
            info_text += f"""
Pattern {i+1}:
  • Points: {len(spray_points)}
  • Height: {spray_height} mm
  • Fan Speed: {fan_speed}%
"""
    
    # Main contour settings
    main_settings = workpiece['contour'].get('settings', {})
    if main_settings:
        info_text += f"""

MAIN CONTOUR SETTINGS
─────────────────────
• Spray Width: {main_settings.get('Spray Width', 'N/A')} mm
• Height: {main_settings.get('Spraying Height', 'N/A')} mm
• Velocity: {main_settings.get('Velocity', 'N/A')} mm/s
• Acceleration: {main_settings.get('Acceleration', 'N/A')} mm/s²
"""
    
    ax_info.text(0.05, 0.95, info_text, transform=ax_info.transAxes, 
                fontsize=10, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8))
    
    plt.tight_layout()
    
    # Save the plot
    output_path = Path(json_path).parent / f"{Path(json_path).stem}_visualization.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"📊 Visualization saved to: {output_path}")
    
    # Show the plot
    plt.show()
    
    return fig

if __name__ == "__main__":
    # Path to the workpiece JSON file
    json_path = "/home/plp/cobot-soft-v2.1.2/cobot-glue-dispencing-v2/cobot-soft-glue-dispencing-v2/GlueDispensingApplication/storage/workpieces/2025-10-13/2025-10-13_10-19-13-558000/2025-10-13_10-19-13-558000_workpiece.json"
    
    print("🔍 Loading workpiece visualization...")
    fig = visualize_workpiece(json_path)
    print("✅ Visualization complete!")