from matplotlib import pyplot as plt
from PyQt6.QtWidgets import QMessageBox


class DataExportManager:
    def __init__(self, editor):
        self.editor = editor

    def save_robot_path_dict_to_txt(self, filename="robot_path_dict.txt", samples_per_segment=5):
        """Save robot path as dictionary format to text file"""
        robot_path_dict = self.editor.manager.to_wp_data(samples_per_segment)
        try:
            with open(filename, 'w') as f:
                for segment_name, path in robot_path_dict.items():
                    f.write(f"Segment: {segment_name}\n")
                    for pt in path:
                        f.write(f"{pt.x():.3f}, {pt.y():.3f}\n")
                    f.write("\n")  # Add a blank line between segments
            print(f"Saved path to {filename}")
        except Exception as e:
            print(f"Error saving path: {e}")

        return robot_path_dict

    def save_robot_path_to_txt(self, filename="robot_path.txt", samples_per_segment=5):
        """Save robot path as simple coordinate list to text file"""
        path = self.editor.manager.get_robot_path(samples_per_segment)
        try:
            with open(filename, 'w') as f:
                for pt in path:
                    f.write(f"{pt.x():.3f}, {pt.y():.3f}\n")
            print(f"Saved path to {filename}")
        except Exception as e:
            print(f"Error saving path: {e}")

    def plot_robot_path(self, filename="robot_path.txt"):
        """Plot robot path from text file using matplotlib"""
        try:
            with open(filename, 'r') as f:
                coords = []
                for line in f:
                    line = line.strip()
                    if not line or ',' not in line:
                        continue
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) < 2:
                        continue
                    try:
                        x = float(parts[0])
                        y = float(parts[1])
                        coords.append((x, y))
                    except ValueError:
                        continue

            if not coords:
                QMessageBox.warning(self.editor, "No Points", "No valid points found.")
                return

            # Remove duplicate points while preserving order
            seen = set()
            unique_coords = []
            for c in coords:
                if c not in seen:
                    seen.add(c)
                    unique_coords.append(c)

            x_vals, y_vals = zip(*unique_coords)
            total_points = len(unique_coords)

            plt.figure(figsize=(12.8, 7.2))
            plt.plot(x_vals, y_vals, 'b-', label="Robot Path")
            plt.scatter(x_vals, y_vals, color='red', label=f"Points ({total_points})")
            plt.gca().invert_yaxis()
            plt.xlim(0, self.editor.width())
            plt.ylim(self.editor.height(), 0)
            plt.title(f"Robot Path Visualization (Total Points: {total_points})")
            plt.xlabel("X")
            plt.ylabel("Y")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.show()
        except Exception as e:
            print(f"Failed to plot path: {e}")

    def export_contour_data(self, format_type="json"):
        """Export current contour data in specified format"""
        # Future extension point for different export formats
        if format_type == "json":
            # Could implement JSON export
            pass
        elif format_type == "csv":
            # Could implement CSV export
            pass
        else:
            print(f"Unsupported export format: {format_type}")

    def get_export_statistics(self):
        """Get statistics about the current contour data for export"""
        segments = self.editor.manager.get_segments()
        total_points = sum(len(segment.anchors) for segment in segments)
        
        stats = {
            "total_segments": len(segments),
            "total_points": total_points,
            "layers": list(set(segment.layer.name for segment in segments if hasattr(segment, 'layer')))
        }
        
        return stats