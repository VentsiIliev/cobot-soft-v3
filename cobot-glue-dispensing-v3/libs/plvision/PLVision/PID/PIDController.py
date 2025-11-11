"""
* File: PIDController.py
* Author: IlV
* Comments:
* Revision history:
* Date       Author      Description
* -----------------------------------------------------------------
** 100624     IlV         Initial release
* -----------------------------------------------------------------
*
"""

"""
PID контролерът е механизъм за обратна връзка в контролния цикъл, широко използван в индустриалните контролни системи и множество други приложения, изискващи непрекъснато модулиран контрол. PID означава Пропорционален, Интегрален и Диференциален, което се отнася до трите термина, които действат върху сигнала за грешка, за да произведат контролен изход.

Ето кратко обяснение на променливите в PID контролера:

- `Kp` (Пропорционален коефициент): Пропорционалният термин произвежда изходна стойност, която е пропорционална на текущата грешка. Пропорционалният отговор може да бъде регулиран чрез умножение на грешката с константа `Kp`, наречена константа за пропорционален коефициент.

- `Ki` (Интегрален коефициент): Интегралният термин е пропорционален както на големината на грешката, така и на продължителността на грешката. ��нтегралният отговор се изчислява чрез натрупване на грешката през времето, след което тази натрупана грешка се умножава с `Ki`, интегралният коефициент.

- `Kd` (Диференциален коефициент): Диференциалният термин е пропорционален на скоростта на промяна на грешката. Това означава, че изходът на контролера е под влиянието на скоростта, с която грешката се променя. По-бързата промяна на грешката, по-голям е приносът на диференциалния термин към изхода. Този термин се изчислява чрез определяне на наклона на грешката през времето и умножаване на тази скорост на промяна с диференциалния коефициент `Kd`.

- `target`: Това е желаната стойност за системата, стойността, която искате вашата система да постигне.

- `previous_error`: Това е стойността на грешката в предишния времеви интервал, използвана за изчисляване на диференциала на грешката.

- `integral`: Това е натрупаната грешка през времето, използвана в интегралния термин на PID контролера.

Изходът на PID контролера се изчислява по следния начин:

`output = Kp * error + Ki * integral + Kd * derivative`

Този изход може след това да се използва за корекция на системата (например, корекция на яркостта или контраста на изображение, контрол на скоростта на мотор и т.н.).
"""
class PIDController:
    """
    A simple PID controller.

    Attributes:
        Kp (float): Proportional gain.
        Ki (float): Integral gain.
        Kd (float): Derivative gain.
        target (float): Desired value.
        previousError (float): The error at the previous time step.
        integral (float): Accumulated error over time.
    """

    def __init__(self, Kp, Ki, Kd, target):
        """Initialize the PID controller."""
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.target = target
        self.previousError = 0
        self.integral = 0

    def compute(self, currentValue):
        """
        Compute the output of the PID controller.

        Args:
            currentValue (float): The current value to be controlled.

        Returns:
            float: The output of the PID controller.
        """
        # Calculate the error
        error = self.target - currentValue

        # Accumulate the error over time
        self.integral += error

        # Calculate the change in error
        derivative = error - self.previousError

        # Compute the output
        output = self.Kp * error + self.Ki * self.integral + self.Kd * derivative

        # Update the previous error
        self.previousError = error

        return output