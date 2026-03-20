#include "AccelStepper.h"
#include "MultiStepper.h"
#include <Arduino.h>
#include <math.h>
#include <utility>
#include <Servo.h>
#include <string>
#include <vector>
#include <sstream>

#define SQUARE_SIZE_MM 50.8  // Size of a chess square in millimeters
#define STEP_ANGLE_DEGREES 1.8  // Stepper motor step angle in degrees
#define PULLEY_DIAMETER 12.0  // Pulley diameter in millimeters
#define CIRCUMFERENCE (PULLEY_DIAMETER * PI)
#define MICROSTEPPING 8.0
#define DEADZONE_MM 24  // Deadzone in millimeters for movement commands

#define STEP_PIN_1 D0
#define DIR_PIN_1 D1
#define STEP_PIN_2 D2
#define DIR_PIN_2 D3
#define PLAY_PIN D7

#define SERVO_PIN D6
#define MOVE_BUTTON D7
#define LED_PIN D8

#define LIMIT_SWITCH_1 D4
#define LIMIT_SWITCH_2 D5

#define HOME_SPEED 4000
#define MOVE_SPEED 4000  // Speed for homing in steps per second

AccelStepper stepper1(AccelStepper::DRIVER, STEP_PIN_1, DIR_PIN_1); // step, dir pins
AccelStepper stepper2(AccelStepper::DRIVER, STEP_PIN_2, DIR_PIN_2); // step, dir pins
MultiStepper steppers;

int servoGrabPosition = -3; // Servo position to grab piece0
int servoReleasePosition = 85; // Servo position to release piece
static bool isFastHome = false;
bool button_pressed = false;
struct Position{
    float x;
    float y;
};
struct Data{
    Position pos;
    bool active_magnet;
};

Position current_position;
Position drop_position = {0.5, 5.5};

std::pair<float, float> get_steps(float delta_x, float delta_y);

void IRAM_ATTR onPlayButtonPress() {
    // This function will be called when the play button is pressed
    button_pressed = true;

}

void go_to_position (Position pos);
void goHome();
void reset_position();
void grab_piece(bool state);
void release_piece(bool state);
void move_distance(float delta_x, float delta_y);
void drop_piece();

Servo myServo;

void setup() {
    Serial.begin(115200);

    pinMode(LIMIT_SWITCH_1, INPUT);
    pinMode(LIMIT_SWITCH_2, INPUT);
    pinMode(LED_PIN, OUTPUT);
    pinMode(SERVO_PIN, OUTPUT);
    pinMode(PLAY_PIN, INPUT_PULLDOWN);
    
    stepper1.setMaxSpeed(MOVE_SPEED);
    stepper1.setAcceleration(500);
    stepper2.setMaxSpeed(MOVE_SPEED);
    stepper2.setAcceleration(500);
    steppers.addStepper(stepper1);
    steppers.addStepper(stepper2);

    attachInterrupt(PLAY_PIN, onPlayButtonPress, RISING);
    myServo.attach(SERVO_PIN);
    goHome();
    myServo.write(servoReleasePosition); // Ensure servo is in release position
    reset_position();

}

enum CommandType {
    CHESSMOVE,
    MOVE,
    HOME,
    JOG,
    STOP,
    PATH,
    SERVO
};

CommandType parseCommand(String cmd) {
    if (cmd == "CHESSMOVE") return CHESSMOVE;
    if (cmd == "MOVE") return MOVE;
    if (cmd == "HOME") return HOME;
    if (cmd == "STOP") return STOP;
    if (cmd == "JOG")  return JOG;
    if (cmd == "PATH")  return PATH;
    if(cmd == "SERVO") return SERVO;

    return STOP;
}

// Helper function to extract command (uppercase letters at start)
String extractCommand(String input) {
    String cmd = "";
    for (int i = 0; i < input.length(); i++) {
        char c = input[i];
        if (c >= 'A' && c <= 'Z') {
            cmd += c;
        } else {
            break;
        }
    }
    return cmd;
}

// Helper function to parse coordinate data from pipe-separated format
// Format: "|x,y,magnet" or "x,y,magnet"
bool parseCoordinates(String data, float& x, float& y, bool& magnet) {
    // Remove leading '|' if present
    if (data[0] == '|') {
        data = data.substring(1);
    }
    
    int firstComma = data.indexOf(',');
    int secondComma = data.indexOf(',', firstComma + 1);
    
    if (firstComma == -1 || secondComma == -1) {
        return false;
    }
    
    x = data.substring(0, firstComma).toFloat();
    y = data.substring(firstComma + 1, secondComma).toFloat();
    magnet = data.substring(secondComma + 1).toInt() != 0;
    
    return true;
}

Position parsePosition(String data) {
    // Remove leading '|' if present
    if (data.length() > 0 && data[0] == '|') {
        data = data.substring(1);
    }
    
    // Parse pipe-separated format: "x|y"
    int pipeIndex = data.indexOf('|');
    if (pipeIndex == -1) {
        return {0, 0}; // Invalid format
    }
    
    float x = data.substring(0, pipeIndex).toFloat();
    float y = data.substring(pipeIndex + 1).toFloat();

    return {x, y};
}

// Helper function to parse PATH command with multiple coordinate sets
std::vector<std::string> splitByPipe(String input) {
    std::vector<std::string> result;
    int start = 0;
    
    for (int i = 0; i <= input.length(); i++) {
        if (i == input.length() || input[i] == '|') {
            if (i > start) {
                String segment = input.substring(start, i);
                result.push_back(std::string(segment.c_str()));
            }
            start = i + 1;
        }
    }
    
    return result;
}

void loop() {
    if (button_pressed){
        Serial.println("PLAYED");
        button_pressed = false;
    }

    if (Serial.available() > 0) 
    {
        String input = Serial.readStringUntil('\n');
        input.trim();

        // Extract command (uppercase letters at start)
        String commandString = extractCommand(input);
        CommandType commandType = parseCommand(commandString);
        String dataString = input.substring(commandString.length());

        float posX = current_position.x;
        float posY = current_position.y;
        bool magnetState = false;

        switch (commandType) 
        {
            case CommandType::PATH: {
                // Parse format: "PATH|x,y,magnet|x,y,magnet|..."
                std::vector<std::string> segments = splitByPipe(input.substring(4)); // Skip "PATH"
                
                for (const auto& segment : segments) {
                    if (segment.empty()) continue;
                    
                    String segStr(segment.c_str());
                    if (parseCoordinates(segStr, posX, posY, magnetState)) {
                        posX = posX * SQUARE_SIZE_MM;
                        posY = posY * SQUARE_SIZE_MM;
                        go_to_position({posX, posY});
                        if ((abs(posX - drop_position.x*SQUARE_SIZE_MM)) < 0.01 && (abs(posY - drop_position.y*SQUARE_SIZE_MM)) < 0.01) {
                            drop_piece();
                        }
                        grab_piece(magnetState);
                        digitalWrite(LED_PIN, magnetState);
                    }
                }
                Serial.println("DONE");
                break;
            }
            
            case CommandType::CHESSMOVE: {
                // Parse format: "CHESSMOVE x,y,magnet"
                String dataStr = input.substring(9); // Skip "CHESSMOVE"
                if (parseCoordinates(dataStr, posX, posY, magnetState)) {
                    posX = posX * SQUARE_SIZE_MM;
                    posY = posY * SQUARE_SIZE_MM;

                    go_to_position({posX, posY});
                    if ((posX == drop_position.x*SQUARE_SIZE_MM) && (posY == drop_position.y*SQUARE_SIZE_MM)) {
                        drop_piece();
                    }
                    grab_piece(magnetState);
                    digitalWrite(LED_PIN, magnetState);
                }
                Serial.println("DONE");
                break;
            }

            case CommandType::MOVE:
                Position targetPos; 
                targetPos = parsePosition(dataString);
                go_to_position({targetPos.x, targetPos.y});
                Serial.println("DONE");
                break;    

            case CommandType::JOG:
                Position deltaPos;
                deltaPos = parsePosition(dataString);
                move_distance(deltaPos.x, deltaPos.y);
                Serial.println("DONE");
                break;
        
            case CommandType::HOME:
                grab_piece(false);
                goHome();
                Serial.println("HOMED");
                break;

            case CommandType::STOP:
                grab_piece(false);
                stepper1.stop();
                stepper2.stop();
                Serial.println("STOPPED");
                break;
            
            case CommandType::SERVO:
                // Get magnet state from input
                magnetState = input.substring(5).toInt() != 0;
                grab_piece(magnetState);
                Serial.print("SERVO");
                break;
        }
    }
}

void reset_position() {
    
    stepper1.setCurrentPosition(0);
    stepper2.setCurrentPosition(0);
    current_position = {0.5*SQUARE_SIZE_MM, 0.5*SQUARE_SIZE_MM}; 
}

void grab_piece(bool state) {
    // Activate magnet to grab piece
    static bool last_state = false;
    if (state == last_state) return;
    last_state = state;
    if (state) {
        myServo.write(servoGrabPosition);
    } else {
        myServo.write(servoReleasePosition);
    }
    delay(250); // Small delay to ensure magnet state change
}

std::pair<float, float> get_steps(float delta_x, float delta_y) {
    // Calculate the number of steps needed for each axis
    
    float rot_step1 = -360.0 * (delta_x + delta_y) / (CIRCUMFERENCE * sqrt(2));
    float rot_step2 = -((2*delta_x * 360/(CIRCUMFERENCE * sqrt(2))) + rot_step1);
    float step_mot1 = (rot_step1 * MICROSTEPPING * 1.333) / (STEP_ANGLE_DEGREES);
    float step_mot2 = (rot_step2 * MICROSTEPPING * 1.333)/ (STEP_ANGLE_DEGREES);
    
    return std::make_pair(-step_mot1, -step_mot2);
}

/*
This fonction move the head of the core XY to an absolute position
*/
void go_to_position (Position pos) { 

    float delta_x = -(pos.x - current_position.x);
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
    std::pair<float, float> steps = get_steps(-delta_x, delta_y);
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

void goHome() {

    myServo.write(servoReleasePosition); // Ensure servo is in release position
    while(digitalRead(LIMIT_SWITCH_2) == LOW) 
    {
        stepper1.setSpeed(-HOME_SPEED); // Move towards home
        stepper2.setSpeed(HOME_SPEED); // Move towards home
        stepper1.run();
        stepper2.run();
    }

    stepper1.stop();
    stepper2.stop();
    move_distance(0.0, 2.0); // Move away from limit switches

    while(digitalRead(LIMIT_SWITCH_1) == LOW)
    {
        stepper1.setSpeed(HOME_SPEED); // Move towards home
        stepper2.setSpeed(HOME_SPEED); // Move towards home
        stepper1.run();
        stepper2.run();
    }
    stepper1.stop();
    stepper2.stop();
    move_distance((SQUARE_SIZE_MM/2), 0.0); // Move away from limit switches
    reset_position();
}

void drop_piece() {
    go_to_position({0.5*SQUARE_SIZE_MM, SQUARE_SIZE_MM*5.5+2});
    go_to_position({-2, SQUARE_SIZE_MM*5.5+2});
    go_to_position({-2, SQUARE_SIZE_MM*4.5+2});
}

