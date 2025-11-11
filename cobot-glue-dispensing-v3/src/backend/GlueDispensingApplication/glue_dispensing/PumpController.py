from modules.shared.shared.settings.conreateSettings.enums.GlueSettingKey import GlueSettingKey
from src.backend.GlueDispensingApplication.utils.custom_logging import log_debug_message, log_error_message, LoggerContext


class PumpController:
    def __init__(self, use_segment_settings: bool, logger_context: LoggerContext = None):
        """
        Handles motor (pump) control logic for glue dispensing operations.
        """
        self.use_segment_settings = use_segment_settings
        self.logger_context = logger_context

    def pump_on(self, service, robot_service, glue_type, settings=None):
        """
        Turn on the pump motor using either segment-specific or global settings.
        """
        effective_settings = settings if self.use_segment_settings else None
        return self.__pump_on(
            service=service,
            robot_service=robot_service,
            glue_type=glue_type,
            settings=effective_settings,
        )

    def pump_off(self, service, robot_service, glue_type, settings=None):
        """
        Turn off the pump motor using either segment-specific or global settings.
        """
        effective_settings = settings if self.use_segment_settings else None
        self.__pump_off(
            service=service,
            robot_service=robot_service,
            glue_type=glue_type,
            settings=effective_settings,
        )

    def __pump_on(self, service, robot_service, glue_type, settings=None):
        """
        Internal method to handle motorOn using either global or segment settings.
        Returns True/False based on success.
        """


        try:
            if settings is None:
                # Using global settings
                result = service.motorOn(
                    motorAddress=glue_type,
                    speed=robot_service.settingsService.glue_settings.get_motor_speed(),
                    ramp_steps=robot_service.settingsService.glue_settings.get_forward_ramp_steps(),
                    initial_ramp_speed=robot_service.settingsService.glue_settings.get_initial_ramp_speed(),
                    initial_ramp_speed_duration=robot_service.settingsService.glue_settings.get_initial_ramp_speed_duration(),
                )
                log_debug_message(
                    self.logger_context,
                    message=f"Pump ON (global): speed={robot_service.settingsService.glue_settings.get_motor_speed()}",
                )
            else:
                # Using segment settings
                result = service.motorOn(
                    motorAddress=glue_type,
                    speed=float(settings.get(GlueSettingKey.MOTOR_SPEED.value, 0)),
                    ramp_steps=int(float(settings.get(GlueSettingKey.FORWARD_RAMP_STEPS.value, 0))),
                    initial_ramp_speed=float(settings.get(GlueSettingKey.INITIAL_RAMP_SPEED.value, 0)),
                    initial_ramp_speed_duration=float(
                        settings.get(GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value, 0)
                    ),
                )
                log_debug_message(
                    self.logger_context,
                    message=f"Pump ON (segment): {settings}",
                )

            return result

        except Exception as e:
            log_error_message(self.logger_context, message=f"Pump ON failed: {e}")
            return False

    def __pump_off(self, service, robot_service, glue_type, settings=None):
        """
        Internal method to handle motorOff using either global or segment settings.
        """


        try:
            if settings is None:
                # Using global settings
                service.motorOff(
                    motorAddress=glue_type,
                    speedReverse=robot_service.settingsService.glue_settings.get_speed_reverse(),
                    reverse_time=robot_service.settingsService.glue_settings.get_steps_reverse(),
                    ramp_steps=robot_service.settingsService.glue_settings.get_reverse_ramp_steps(),
                )
                log_debug_message(
                    self.logger_context,
                    message="Pump OFF (global settings)",
                )
            else:
                # Using segment settings
                service.motorOff(
                    motorAddress=glue_type,
                    speedReverse=float(settings.get(GlueSettingKey.SPEED_REVERSE.value, 0)),
                    reverse_time=float(settings.get(GlueSettingKey.REVERSE_DURATION.value, 0)),
                    ramp_steps=int(float(settings.get(GlueSettingKey.REVERSE_RAMP_STEPS.value, 0))),
                )
                log_debug_message(
                    self.logger_context,
                    message=f"Pump OFF (segment): {settings}",
                )

        except Exception as e:
            log_error_message(self.logger_context, message=f"Pump OFF failed: {e}")
