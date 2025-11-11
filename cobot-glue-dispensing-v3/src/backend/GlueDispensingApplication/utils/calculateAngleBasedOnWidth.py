import math

# --- 1. Get angle (in degrees) from Y and magnitude ---
def get_angle_from_y(y, magnitude):
    """Returns the angle (in degrees) given y-component and magnitude."""
    return math.degrees(math.asin(y / magnitude))

# --- 2. Get angle (in degrees) from X and magnitude ---
def get_angle_from_x(x, magnitude):
    """Returns the angle (in degrees) given x-component and magnitude."""
    return math.degrees(math.acos(x / magnitude))

# --- 3. Get X from angle (in degrees) and magnitude ---
def get_x_from_angle(angle_deg, magnitude):
    """Returns the x-component given angle (deg) and magnitude."""
    angle_rad = math.radians(angle_deg)
    return magnitude * math.cos(angle_rad)

# --- 4. Get Y from angle (in degrees) and magnitude ---
def get_y_from_angle(angle_deg, magnitude):
    """Returns the y-component given angle (deg) and magnitude."""
    angle_rad = math.radians(angle_deg)
    return magnitude * math.sin(angle_rad)


import math

# clearer constants
SPRAY_ALONG_X = 0
SPRAY_ALONG_Y = 1

def get_angle_from_width(desired_width, transducer_magnitude, spray_along_axis):
    """Return angle in degrees to achieve desired_width on the specified axis."""
    if spray_along_axis == SPRAY_ALONG_X:
        return get_angle_from_x(desired_width, transducer_magnitude)
    elif spray_along_axis == SPRAY_ALONG_Y:
        return get_angle_from_y(desired_width, transducer_magnitude)
    else:
        raise ValueError("Invalid spray_along_axis; use SPRAY_ALONG_X or SPRAY_ALONG_Y")

# example usage
if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import numpy as np
    
    transducer_magnitude = 25.0
    for desired_width in range(0, 26):
        ax = get_angle_from_width(desired_width, transducer_magnitude, SPRAY_ALONG_X)
        ay = get_angle_from_width(desired_width, transducer_magnitude, SPRAY_ALONG_Y)
        print(f"desired_width={desired_width:5.2f} -> angle for X: {ax:6.2f}°, angle for Y: {ay:6.2f}°")
        
        # Create visualization for each iteration
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Plot 1: Vector representation for X-axis spray
        angles_x = np.linspace(0, ax, 100)
        x_components = [get_x_from_angle(angle, transducer_magnitude) for angle in angles_x]
        y_components = [get_y_from_angle(angle, transducer_magnitude) for angle in angles_x]
        
        ax1.plot(x_components, y_components, 'b-', linewidth=2, label='Spray vector path')
        ax1.plot([0, desired_width], [0, 0], 'ro-', linewidth=3, markersize=8, label=f'Target width: {desired_width}')
        ax1.arrow(0, 0, desired_width, get_y_from_angle(ax, transducer_magnitude), 
                 head_width=0.5, head_length=0.5, fc='red', ec='red', alpha=0.7)
        ax1.set_xlim(-2, transducer_magnitude + 2)
        ax1.set_ylim(-2, transducer_magnitude + 2)
        ax1.set_xlabel('X Component (width)')
        ax1.set_ylabel('Y Component')
        ax1.set_title(f'Spray Along X-Axis\nWidth: {desired_width}, Angle: {ax:.2f}°')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        ax1.set_aspect('equal')
        
        # Plot 2: Vector representation for Y-axis spray
        angles_y = np.linspace(0, ay, 100)
        x_components_y = [get_x_from_angle(angle, transducer_magnitude) for angle in angles_y]
        y_components_y = [get_y_from_angle(angle, transducer_magnitude) for angle in angles_y]
        
        ax2.plot(x_components_y, y_components_y, 'g-', linewidth=2, label='Spray vector path')
        ax2.plot([0, 0], [0, desired_width], 'ro-', linewidth=3, markersize=8, label=f'Target width: {desired_width}')
        ax2.arrow(0, 0, get_x_from_angle(ay, transducer_magnitude), desired_width, 
                 head_width=0.5, head_length=0.5, fc='red', ec='red', alpha=0.7)
        ax2.set_xlim(-2, transducer_magnitude + 2)
        ax2.set_ylim(-2, transducer_magnitude + 2)
        ax2.set_xlabel('X Component')
        ax2.set_ylabel('Y Component (width)')
        ax2.set_title(f'Spray Along Y-Axis\nWidth: {desired_width}, Angle: {ay:.2f}°')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        ax2.set_aspect('equal')
        
        # Add magnitude circle for reference
        circle_x = np.linspace(0, 2*np.pi, 100)
        circle_x_coords = transducer_magnitude * np.cos(circle_x)
        circle_y_coords = transducer_magnitude * np.sin(circle_x)
        ax1.plot(circle_x_coords, circle_y_coords, 'k--', alpha=0.3, label=f'Max magnitude: {transducer_magnitude}')
        ax2.plot(circle_x_coords, circle_y_coords, 'k--', alpha=0.3, label=f'Max magnitude: {transducer_magnitude}')
        
        plt.suptitle(f'Spray Angle Calculation - Iteration {desired_width + 1}/26')
        plt.tight_layout()
        
        # Show plot and wait for user interaction (blocking)
        plt.show(block=True)
        
        # Close the figure to free memory
        plt.close()


