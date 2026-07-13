#include <MeMegaPi.h>

MeUltrasonicSensor ultra1(PORT_6);
MeUltrasonicSensor ultra2(PORT_8);
MeMegaPiDCMotor motorM1(PORT1B);
MeMegaPiDCMotor motorM4(PORT4B);

MePort port(PORT_7);
Servo servo;
int16_t servoPin =  port.pin1();

//Inclusion of the motors and sensors in their corresponding pins

int velocity = 100;
//Predefined velocity value

short forward = 1; 
//Direction or rotation of the motors 

int rotation = 90;

int rotationSpeed = 2;

short direction = 1;

char incomingCommand = ' ';
// Variable to store the command received from Python

void setup() {
  servo.attach(servoPin);

  Serial.begin(9600);
  Serial.println("System initialized");
  //Serial connection
}

void loop() {
  if (Serial.available() > 0) {
    incomingCommand = Serial.read();
    Serial.print("Command received: "); Serial.println(incomingCommand);
      // Read the command (If there is data on the serial port)
  }

  if (incomingCommand == 'D') {
    //Command 'D' (Stop)

    motorM1.run(0); motorM4.run(0);
    //The robot remains still while the command is D
  } 
  else {
    if (incomingCommand == 'A') {
      //Execute the advance command

      incomingCommand = ' ';
      //Reset to neutral state to allow navigation
    }

    float dist1 = ultra1.distanceCm();
    float dist2 = ultra2.distanceCm();
    //Set distance as a decimal value

    Serial.print("D1: "); Serial.print(dist1);
    Serial.print(" | D2: "); Serial.print(dist2);
    Serial.print(" | Direction: "); Serial.println(forward);
    //Prints a message regarding distances and the direction it follows

    if (forward == 1) {
      if (dist1 < 20 && dist1 > 0){
        Serial.println("Obstacle in front: Reversing");
        forward = -1;
        delay(500);
        //Function to identify and trigger motor rotation changes when an obstacle is detected at 20cm
      }
    } 
    else {
      if (dist2 < 20 && dist2 > 0){
        Serial.println("Obstacle behind: Moving forward");
        forward = 1;
        delay(500); 
        //Function to identify and trigger motor rotation changes (to opposite direction) when an obstacle is detected at 20cm
      }
    }

    motorM1.run(-velocity * forward);
    motorM4.run(velocity * forward);
    //Velocity adjustment for each motor

    if (rotation >= 180) direction = -1;
    else if (rotation <= 0) direction = 1;
    rotation += rotationSpeed * direction;
    servo.write(rotation);
  }

  delay(50);
}
