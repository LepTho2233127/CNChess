#include <AccelStepper.h>
#include <MultiStepper.h>
#include <Arduino.h>

AccelStepper stepper1(AccelStepper::DRIVER, 2, 3); // step, dir pins
AccelStepper stepper2(AccelStepper::DRIVER, 4, 5); // step, dir pins
MultiStepper steppers;
long targetPos_stepper1 = 0;
long targetPos_stepper2 = 0;

int limit_switch_x = 8; // Pin for limit switch of stepper 1
int limit_switch_y = 9; // Pin for limit switch of stepper 2
long positions[2] = {0, 0}; 

void setup() {
    Serial.begin(115200);
    stepper1.setMaxSpeed(1000);
    stepper1.setAcceleration(500);
    stepper2.setMaxSpeed(1000);
    stepper2.setAcceleration(500);
    steppers.addStepper(stepper1);
    steppers.addStepper(stepper2);
    pinMode(limit_switch_x, INPUT);
    pinMode(limit_switch_y, INPUT);
}

enum CommandType {
    MOVE,
    HOME,
    STOP
};

CommandType parseCommand(String cmd) {
    if (cmd == "MOVE") return MOVE;
    if (cmd == "HOME") return HOME;
    if (cmd == "STOP") return STOP;

    return STOP;
}

void loop() {
    if (Serial.available() > 0) 
    {
        String input = Serial.readStringUntil('\n');
        
        // Parse format: "MOVE x y"
        int firstSpace = input.indexOf(' ');
        int secondSpace = input.indexOf(' ', firstSpace + 1);
        
        String commandString = input.substring(0, firstSpace);
        targetPos_stepper1 = input.substring(firstSpace + 1, secondSpace).toInt();
        targetPos_stepper2 = input.substring(secondSpace + 1).toInt();
        
        positions[0] = targetPos_stepper1;
        positions[1] = targetPos_stepper2;
        // Utiliser commandType selon le besoin

        // Attendre que les steppers terminent leur mouvement
        CommandType commandType = parseCommand(commandString);

        switch (commandType) 
        {
            case CommandType::MOVE: 
                steppers.moveTo(positions);
                steppers.runSpeedToPosition();
                break;
        
            case CommandType::HOME:
                while(digitalRead(limit_switch_x) == LOW)
                {
                    stepper1.setSpeed(-200); // Move towards home
                    stepper2.setSpeed(-200); // Move towards home
                    stepper1.run();
                    stepper2.run();
                }
                while(digitalRead(limit_switch_y) == LOW)
                {
                    stepper1.setSpeed(-200); // Move towards home
                    stepper2.setSpeed(200); // Move towards home
                    stepper1.run();
                    stepper2.run();
                }
                stepper1.stop();
                stepper2.stop();
                stepper1.setCurrentPosition(0);
                stepper2.setCurrentPosition(0);
                Serial.println("HOMED");
                break;

            case CommandType::STOP:
                stepper1.stop();
                stepper2.stop();
                break;
            
        }
    }

    if (steppers.run()) {
        stepper1.run();
        stepper2.run();
    } else {
        Serial.println("DONE");
    }
}


