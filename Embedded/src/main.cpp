#include <AccelStepper.h>
#include <MultiStepper.h>
#include <Arduino.h>
#include <math.h>
#include <utility>
#include <Servo.h>

#define SQUARE_SIZE_MM 50.8  // Size of a chess square in millimeters
#define STEP_ANGLE_DEGREES 1.8  // Stepper motor step angle in degrees
#define PULLEY_DIAMETER 12.0  // Pulley diameter in millimeters
#define CIRCUMFERENCE (PULLEY_DIAMETER * PI)
#define MICROSTEPPING 8.0
#define DEADZONE_MM 25.4  // Deadzone in millimeters for movement commands

#define STEP_PIN_1 D0
#define DIR_PIN_1 D1
#define STEP_PIN_2 D2
#define DIR_PIN_2 D3

#define SERVO_PIN D6

#define LIMIT_SWITCH_1 D4
#define LIMIT_SWITCH_2 D5

AccelStepper stepper1(AccelStepper::DRIVER, STEP_PIN_1, DIR_PIN_1); // step, dir pins
AccelStepper stepper2(AccelStepper::DRIVER, STEP_PIN_2, DIR_PIN_2); // step, dir pins
MultiStepper steppers;

int servoGrabPosition = 0; // Servo position to grab piece0
int servoReleasePosition = 170; // Servo position to release piece170
static bool isFastHome = false;

struct Position{
    float x;
    float y;
};
struct Data{
    Position pos;
    bool active_magnet;
};

Position current_position;

std::pair<float, float> get_steps(float delta_x, float delta_y);

void go_to_position (Position pos);
void goHome(bool isFastHome);
void reset_position();
void grab_piece(bool state);
void release_piece(bool state);

Servo myServo;

void setup() {
    Serial.begin(115200);

    pinMode(LIMIT_SWITCH_1, INPUT);
    pinMode(LIMIT_SWITCH_2, INPUT);
    pinMode(SERVO_PIN, OUTPUT);
    
    stepper1.setMaxSpeed(2500);
    stepper1.setAcceleration(500);
    stepper2.setMaxSpeed(2500);
    stepper2.setAcceleration(500);
    steppers.addStepper(stepper1);
    steppers.addStepper(stepper2);

    myServo.attach(SERVO_PIN);
    //myServo.write(servoGrabPosition); // Ensure servo is in release position
    goHome(0);
    //myServo.write(servoReleasePosition); // Ensure servo is in release position
    reset_position();
    //struct Position position1 = {0.0, -150.0};
    // go_to_position(current_position);

}

enum CommandType {
    CHESSMOVE,
    MOVE,
    HOME,
    JOG,
    STOP
};

CommandType parseCommand(String cmd) {
    if (cmd == "CHESSMOVE") return CHESSMOVE;
    if (cmd == "MOVE") return MOVE;
    if (cmd == "HOME") return HOME;
    if (cmd == "STOP") return STOP;
    if (cmd == "JOG")  return JOG;

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
        float posX = input.substring(firstSpace + 1, secondSpace).toFloat();
        float posY = input.substring(secondSpace + 1).toFloat(); 
        bool magnetState = input.substring(secondSpace + 1, thirdSpace).toInt() == 1;
        
        
        CommandType commandType = parseCommand(commandString);

        switch (commandType) 
        {
            case CommandType::CHESSMOVE: 
                posX = posX * SQUARE_SIZE_MM;
                posY = posY * SQUARE_SIZE_MM;
                go_to_position({posX, posY});
                grab_piece(magnetState);
                if (!isFastHome){
                    isFastHome = true;
                }
                Serial.print("DONE");
                break;

            case CommandType::MOVE:
                go_to_position({posX, posY});
                Serial.print("DONE");
                break;    

            case CommandType::JOG:
                move_distance(posX, posY);
                Serial.print("DONE");
                break;
        
            case CommandType::HOME:
                grab_piece(false);
                goHome(isFastHome);
                if (isFastHome){
                    isFastHome = false;
                }
                Serial.print("HOMED");
                break;

            case CommandType::STOP:
                grab_piece(false);
                stepper1.stop();
                stepper2.stop();
                Serial.print("STOPPED");
                break;
            
        }
    }

}

void reset_position() {
    stepper1.setCurrentPosition(0);
    stepper2.setCurrentPosition(0);
    current_position = {0.0, 0.0};
}

void grab_piece(bool state) {
    // Activate magnet to grab piece
    if (state) {
        myServo.write(servoGrabPosition);
    } else {
        myServo.write(servoReleasePosition);
    }
}

std::pair<float, float> get_steps(float delta_x, float delta_y) {
    // Calculate the number of steps needed for each axis
    
    float rot_step1 = -360.0 * (delta_x + delta_y) / (CIRCUMFERENCE * sqrt(2));
    float rot_step2 = -((2*delta_x * 360/(CIRCUMFERENCE * sqrt(2))) + rot_step1);
    float step_mot1 = (rot_step1 * MICROSTEPPING * 1.333) / (STEP_ANGLE_DEGREES);
    float step_mot2 = (rot_step2 * MICROSTEPPING * 1.333)/ (STEP_ANGLE_DEGREES);
    
    return std::make_pair(step_mot1, step_mot2);
}

/*
This fonction move the head of the core XY to an absolute position
*/
void go_to_position (Position pos) { 

    float delta_x = pos.x - current_position.x;
    float delta_y = pos.y - current_position.y;
    std::pair<float, float> steps = get_steps(delta_x, delta_y);
    long positions[2];
    positions[0] = static_cast<long>(steps.first) + stepper1.currentPosition();
    positions[1] = static_cast<long>(steps.second) + stepper2.currentPosition();
    steppers.moveTo(positions);
    steppers.runSpeedToPosition();
    current_position = pos; 
}

/*
This fonction move the head of the core XY by a relative distance
*/
void move_distance(float delta_x, float delta_y) {
    std::pair<float, float> steps = get_steps(delta_x, delta_y);
    long positions[2];
    positions[0] = static_cast<long>(steps.first);
    positions[1] = static_cast<long>(steps.second);
    stepper1.move(positions[0]);
    stepper2.move(positions[1]);
    while (stepper1.isRunning() || stepper2.isRunning()) {
        stepper1.run();
        stepper2.run();
    }
    current_position.x += delta_x;
    current_position.y += delta_y;
}


void goHome(bool isFastHome) {

// Move Y axis towards home first
    if (isFastHome){
        move_distance(0.0, (-current_position.y + 100.0)); // Move towards home quickly
    }
    while(digitalRead(LIMIT_SWITCH_2) == LOW) 
    {
        stepper1.setSpeed(-500); // Move towards home
        stepper2.setSpeed(500); // Move towards home
        stepper1.run();
        stepper2.run();
    }

    stepper1.stop();
    stepper2.stop();
    reset_position();
    move_distance(0.0, -5.0); // Move away from limit switches

// Move X axis towards home
    if (isFastHome){
        move_distance((-current_position.x + 100.0), 0.0); // Move towards home quickly
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
    reset_position();   
    move_distance(-5.0, 0.0); // Move away from limit switches
    reset_position();

}

