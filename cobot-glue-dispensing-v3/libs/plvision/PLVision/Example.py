# from Camera import Camera
# from PID.BrightnessController import BrightnessController
#
# # Създаване на обект от тип Camera
# camera = Camera(0, 1920, 1080)
#
# # Създаване на обект от тип BrightnessController
# brightnessController = BrightnessController(0.5, 0.1, 0.1, 200)
#
# # Заснемане на кадър от камерата
# frame = camera.capture()
#
# # Изчисляване на текущата яркост на кадъра
# currentBrightness = brightnessController.calculateBrightness(frame)
#
# # Изчисляване на корекцията, която трябва да се приложи, за да се достигне желаната яркост
# adjustment = brightnessController.compute(currentBrightness)
#
# # Прилагане на корекцията към кадъра
# adjustedFrame =  brightnessController.adjustBrightness(frame, 100)