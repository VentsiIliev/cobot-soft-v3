# contour_editor/modes/state_machine.py
class EditorStateMachine:
    def __init__(self, editor):
        self.editor = editor
        self.modes = {}
        self.current = None

    def register_mode(self, mode):
        self.modes[mode.name] = mode

    def set_mode(self, name):
        if self.current:
            self.current.exit(self.editor)
        self.current = self.modes.get(name)
        if self.current:
            self.current.enter(self.editor)
        else:
            print(f"⚠️ Mode '{name}' not found")

    # --- Proxy all input events ---
    def mousePress(self, event):
        if self.current:
            self.current.mousePress(self.editor, event)

    def mouseMove(self, event):
        if self.current:
            self.current.mouseMove(self.editor, event)

    def mouseRelease(self, event):
        if self.current:
            self.current.mouseRelease(self.editor, event)

    def wheel(self, event):
        if self.current:
            self.current.wheel(self.editor, event)
