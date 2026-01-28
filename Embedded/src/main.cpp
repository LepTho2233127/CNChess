#include <AccelStepper.h>
#include <MultiStepper.h>
#include <Arduino.h>
#include <math.h>
#include <utility>

#define SQUARE_SIZE_MM 50.8  // Size of a chess square in millimeters
#define STEP_ANGLE_DEGREES 1.8  // Stepper motor step angle in degrees
#define PULLEY_DIAMETER 12.0  // Pulley diameter in millimeters
#define CIRCUMFERENCE (PULLEY_DIAMETER * PI)
#define MICROSTEPPING 8.0

#define STEP_PIN_1 D0
#define DIR_PIN_1 D1
#define STEP_PIN_2 D2
#define DIR_PIN_2 D3


AccelStepper stepper1(AccelStepper::DRIVER, STEP_PIN_1, DIR_PIN_1); // step, dir pins
AccelStepper stepper2(AccelStepper::DRIVER, STEP_PIN_2, DIR_PIN_2); // step, dir pins
MultiStepper steppers;
long targetPos_stepper1 = 0;
long targetPos_stepper2 = 0;

int limit_switch_x = 8; // Pin for limit switch of stepper 1
int limit_switch_y = 9; // Pin for limit switch of stepper 2

struct Position{
    float x;
    float y;
};

Position current_position;

std::pair<float, float> get_steps(Position pos);

void go_to_position (Position pos);

void setup() {
    Serial.begin(115200);
    stepper1.setMaxSpeed(2500);
    stepper1.setAcceleration(500);
    stepper2.setMaxSpeed(2500);
    stepper2.setAcceleration(500);
    steppers.addStepper(stepper1);
    steppers.addStepper(stepper2);
    pinMode(limit_switch_x, INPUT);
    pinMode(limit_switch_y, INPUT);
    current_position = {0.0, 0.0};
    
    struct Position position1 = {0.0, 10.0};
    go_to_position(position1);
    // Serial.println("Reached Position 1");
    // struct Position position2 = {0.0, 1000};
    // go_to_position(position2);
    // Serial.println("Reached Position 2");
    // struct Position position3 = {1000, 0.0};
    // go_to_position(position3);
    // Serial.println("Reached Position 3");
    // struct Position position4 = {0.0, -1000};
    // go_to_position(position4);
    // Serial.println("Reached Position 4");

   

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
    // if (Serial.available() > 0) 
    // {
    //     String input = Serial.readStringUntil('\n');
        
    //     // Parse format: "MOVE x y"
    //     int firstSpace = input.indexOf(' ');
    //     int secondSpace = input.indexOf(' ', firstSpace + 1);
        
    //     String commandString = input.substring(0, firstSpace);
    //     targetPos_stepper1 = input.substring(firstSpace + 1, secondSpace).toInt();
    //     targetPos_stepper2 = input.substring(secondSpace + 1).toInt();
        
    //     positions[0] = targetPos_stepper1;
    //     positions[1] = targetPos_stepper2;
    //     // Utiliser commandType selon le besoin

    //     // Attendre que les steppers terminent leur mouvement
    //     CommandType commandType = parseCommand(commandString);

    //     switch (commandType) 
    //     {
    //         case CommandType::MOVE: 
    //             steppers.moveTo(positions);
    //             steppers.runSpeedToPosition();
    //             break;
        
    //         case CommandType::HOME:
    //             while(digitalRead(limit_switch_x) == LOW)
    //             {
    //                 stepper1.setSpeed(-200); // Move towards home
    //                 stepper2.setSpeed(-200); // Move towards home
    //                 stepper1.run();
    //                 stepper2.run();
    //             }
    //             while(digitalRead(limit_switch_y) == LOW)
    //             {
    //                 stepper1.setSpeed(-200); // Move towards home
    //                 stepper2.setSpeed(200); // Move towards home
    //                 stepper1.run();
    //                 stepper2.run();
    //             }
    //             stepper1.stop();
    //             stepper2.stop();
    //             stepper1.setCurrentPosition(0);
    //             stepper2.setCurrentPosition(0);
    //             Serial.println("HOMED");
    //             break;

    //         case CommandType::STOP:
    //             stepper1.stop();
    //             stepper2.stop();
    //             break;
            
    //     }
    // }

  
}

std::pair<float, float> get_steps(Position pos) {
    // Calculate the number of steps needed for each axis

    float delta_x = pos.x - current_position.x;
    float delta_y = pos.y - current_position.y;

    Serial.println("Delta X: " + String(delta_x) + " Delta Y: " + String(delta_y));

    float rot_step1 = -360.0 * (delta_x + delta_y) / (CIRCUMFERENCE * sqrt(2));
    float rot_step2 = -((2*delta_x * 360/(CIRCUMFERENCE * sqrt(2))) + rot_step1);
    float step_mot1 = rot_step1 / (STEP_ANGLE_DEGREES/MICROSTEPPING);
    float step_mot2 = rot_step2 / (STEP_ANGLE_DEGREES/MICROSTEPPING);

    return std::make_pair(step_mot1, step_mot2);
}

void go_to_position (Position pos) {
    std::pair<float, float> steps = get_steps(pos);
    long positions[2];
    positions[0] = static_cast<long>(steps.first);
    positions[1] = static_cast<long>(steps.second);
    Serial.print("Moving to X: ");
    Serial.print(pos.x);
    Serial.print(" Y: ");
    Serial.print(pos.y);
    steppers.moveTo(positions);
    steppers.runSpeedToPosition();
    current_position = pos;

    while (stepper1.distanceToGo() != 0 || stepper2.distanceToGo() != 0) {
        stepper1.run();
        stepper2.run();
    }
}

