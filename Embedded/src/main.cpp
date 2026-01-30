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

#define LIMIT_SWITCH_1 D4
#define LIMIT_SWITCH_2 D5

AccelStepper stepper1(AccelStepper::DRIVER, STEP_PIN_1, DIR_PIN_1); // step, dir pins
AccelStepper stepper2(AccelStepper::DRIVER, STEP_PIN_2, DIR_PIN_2); // step, dir pins
MultiStepper steppers;

int limit_switch_x = 8; // Pin for limit switch of stepper 1
int limit_switch_y = 9; // Pin for limit switch of stepper 2

struct Position{
    float x;
    float y;
};
struct Data{
    Position pos;
    bool active_magnet;
};

Position current_position;

std::pair<float, float> get_steps(Position pos);

void go_to_position (Position pos);

void goHome();

void setup() {
    Serial.begin(115200);
    stepper1.setMaxSpeed(2500);
    stepper1.setAcceleration(500);
    stepper2.setMaxSpeed(2500);
    stepper2.setAcceleration(500);
    steppers.addStepper(stepper1);
    steppers.addStepper(stepper2);
    pinMode(LIMIT_SWITCH_1, INPUT);
    pinMode(LIMIT_SWITCH_2, INPUT);
    goHome();
    current_position = {0.0, 0.0};
    
    //struct Position position1 = {0.0, -150.0};
    // go_to_position(current_position);

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
        
        // Parse format: "MOVE x y magnet_state"
        int firstSpace = input.indexOf(' ');
        int secondSpace = input.indexOf(' ', firstSpace + 1);
        int thirdSpace = input.indexOf(' ', secondSpace + 1);
        
        String commandString = input.substring(0, firstSpace);
        float posX = input.substring(firstSpace + 1, secondSpace).toFloat() * SQUARE_SIZE_MM;
        float posY = input.substring(secondSpace + 1).toFloat() * SQUARE_SIZE_MM; 
        bool magnetState = false;


        if (thirdSpace != -1) {
            magnetState = input.substring(secondSpace + 1, thirdSpace).toInt() == 1;
        }

        
        CommandType commandType = parseCommand(commandString);

        switch (commandType) 
        {
            case CommandType::MOVE: 
                go_to_position({posX, posY});
                Serial.print("DONE");
                break;
        
            case CommandType::HOME:
                goHome();
                Serial.print("HOMED");
                break;

            case CommandType::STOP:
                stepper1.stop();
                stepper2.stop();
                break;
            
        }
    }

//     go_to_position({0.0, 100});
//     delay(250);
//     go_to_position({100, 100});
//     delay(250);
//     go_to_position({100, -100});
//     delay(250);
//     go_to_position({-100, -100});
//     delay(250);
//     go_to_position({-100, 100});
//     delay(250);
//     go_to_position({0, 100});
//     delay(250);
//     go_to_position({0.0, 0.0});
//     delay(250);
}

std::pair<float, float> get_steps(Position pos) {
    // Calculate the number of steps needed for each axis

    float delta_x = pos.x - current_position.x;
    float delta_y = pos.y - current_position.y;

    float rot_step1 = -360.0 * (delta_x + delta_y) / (CIRCUMFERENCE * sqrt(2));
    float rot_step2 = -((2*delta_x * 360/(CIRCUMFERENCE * sqrt(2))) + rot_step1);
    float step_mot1 = (rot_step1 * MICROSTEPPING * 1.333) / (STEP_ANGLE_DEGREES);
    float step_mot2 = (rot_step2 * MICROSTEPPING * 1.333)/ (STEP_ANGLE_DEGREES);

    return std::make_pair(step_mot1, step_mot2);
}

void go_to_position (Position pos) {
    std::pair<float, float> steps = get_steps(pos);
    long positions[2];
    positions[0] = static_cast<long>(steps.first) + stepper1.currentPosition();
    positions[1] = static_cast<long>(steps.second) + stepper2.currentPosition();
    steppers.moveTo(positions);
    steppers.runSpeedToPosition();
    current_position = pos; 
}

void goHome(){

    bool first_direction = true;

    while(digitalRead(LIMIT_SWITCH_2) == LOW && first_direction)
    {
        stepper1.setSpeed(-500); // Move towards home
        stepper2.setSpeed(500); // Move towards home
        stepper1.run();
        stepper2.run();
    }

    if (digitalRead(LIMIT_SWITCH_2) == HIGH)
    {
        stepper1.stop();
        stepper2.stop();
        first_direction = false;
    }
    
    while(digitalRead(LIMIT_SWITCH_1) == LOW)
    {
        stepper1.setSpeed(-500); // Move towards home
        stepper2.setSpeed(-500); // Move towards home
        stepper1.run();
        stepper2.run();
    }

    stepper1.stop();
    stepper2.stop();
    stepper1.setCurrentPosition(0);
    stepper2.setCurrentPosition(0);
}

