#include <AccelStepper.h>

AccelStepper stepper(AccelStepper::DRIVER, 2, 3); // step, dir pins
long targetPos = 0;

void setup() {
  Serial.begin(115200);
  stepper.setMaxSpeed(1000);
  stepper.setAcceleration(500);
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    targetPos = input.toInt();
    stepper.moveTo(targetPos);
  }

  stepper.run();  // non-blocking motion
}
