# contour_editor/modes/MultiPointSelectMode.py
from PyQt6.QtCore import Qt
from frontend.pl_ui.contour_editor.EditorStateMachine.Modes.BaseMode import BaseMode

class MultiPointSelectMode(BaseMode):
    name = "multi_select"

    def mousePress(self, editor, event, candidates=None):
        if not candidates:
            # Clicked empty space in multi-select mode: do nothing
            print("Multi-select mode: clicked empty space, no point added")
            return

        # Cycle through overlapping points
        if hasattr(editor, "_last_candidates") and editor._last_candidates == candidates:
            editor._last_candidate_index = (editor._last_candidate_index + 1) % len(candidates)
        else:
            editor._last_candidates = candidates
            editor._last_candidate_index = 0

        drag_target = candidates[editor._last_candidate_index]

        # Toggle selection
        editor.selection_manager.toggle_point_selection(drag_target)
        print(f"Multi-select toggled for point: {drag_target}")
