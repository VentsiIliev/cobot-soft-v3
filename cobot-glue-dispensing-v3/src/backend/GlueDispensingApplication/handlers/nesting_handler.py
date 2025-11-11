def start_nesting(application,workpieces):
    from src.GlueDispensingApplication.pick_and_place.nesting import start_nesting
    return start_nesting(
                  visionService=application.visionService,
                  robotService=application.robotService,
                     preselected_workpiece=workpieces,
                         z_offset_for_calibration_pattern = application.settingsManager.get_camera_settings().get_capture_pos_offset())
