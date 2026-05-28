# IVI (In-Vehicle Infotainment) Systems

## Overview
The In-Vehicle Infotainment (IVI) system manages navigation, multimedia, connectivity (CarPlay/Android Auto), voice assistant, HMI frameworks (Qt/Flutter), and runs on Android Automotive OS, QNX, or Linux platforms.

## Platform Architectures

### 1. Android Automotive OS (AAOS)
```java
// VehicleHalService.java - Android Automotive HAL integration
package com.example.ivi;

import android.car.Car;
import android.car.VehiclePropertyIds;
import android.car.hardware.CarPropertyValue;
import android.car.hardware.property.CarPropertyManager;

public class VehicleHalService {
    private CarPropertyManager mCarPropertyManager;

    public void init(Context context) {
        Car car = Car.createCar(context);
        mCarPropertyManager = (CarPropertyManager) car.getCarManager(Car.PROPERTY_SERVICE);

        // Subscribe to vehicle speed updates
        mCarPropertyManager.registerCallback(
            new CarPropertyManager.CarPropertyEventCallback() {
                @Override
                public void onChangeEvent(CarPropertyValue value) {
                    if (value.getPropertyId() == VehiclePropertyIds.PERF_VEHICLE_SPEED) {
                        float speedMs = (Float) value.getValue();
                        updateSpeedUI(speedMs * 3.6f);  // Convert to km/h
                    }
                }

                @Override
                public void onErrorEvent(int propId, int zone) {
                    Log.e("VehicleHal", "Property error: " + propId);
                }
            },
            VehiclePropertyIds.PERF_VEHICLE_SPEED,
            CarPropertyManager.SENSOR_RATE_NORMAL);
    }

    public void setHvacTemperature(float tempCelsius) {
        mCarPropertyManager.setFloatProperty(
            VehiclePropertyIds.HVAC_TEMPERATURE_SET,
            VehicleAreaType.VEHICLE_AREA_TYPE_SEAT,
            tempCelsius);
    }
}
```

### 2. QNX-Based IVI
```c
/* qnx_ivi_service.c - QNX CAR platform integration */
#include <qnxcar/carcontrol.h>
#include <screen/screen.h>

void IVI_QNX_Init(void) {
    /* Initialize QNX CAR framework */
    car_control_t *control = car_control_create();

    /* Register for CAN message callbacks */
    car_control_set_can_callback(control, IVI_CAN_MessageHandler);

    /* Initialize Screen Graphics Subsystem */
    screen_context_t screen_ctx;
    screen_create_context(&screen_ctx, SCREEN_APPLICATION_CONTEXT);

    /* Create display window */
    screen_window_t window;
    screen_create_window(&window, screen_ctx);
    screen_set_window_property_iv(window, SCREEN_PROPERTY_SIZE, (int[]){1920, 1080});
}

void IVI_CAN_MessageHandler(car_can_message_t *msg) {
    if (msg->id == 0x100) {  /* VCU Motor Command */
        uint16_t torque = (msg->data[0] << 8) | msg->data[1];
        IVI_UpdatePowerMeter(torque);
    }
}
```

### 3. Navigation Integration (HERE/TomTom)
```kotlin
// NavigationService.kt - HERE SDK integration
package com.example.ivi.navigation

import com.here.sdk.core.GeoCoordinates
import com.here.sdk.routing.CalculateRouteCallback
import com.here.sdk.routing.Route
import com.here.sdk.routing.RoutingEngine

class NavigationService {
    private lateinit var routingEngine: RoutingEngine

    fun initialize() {
        routingEngine = RoutingEngine()
    }

    fun calculateRoute(
        origin: GeoCoordinates,
        destination: GeoCoordinates,
        callback: (Route?) -> Unit
    ) {
        val waypoints = listOf(
            Waypoint(origin),
            Waypoint(destination)
        )

        val carOptions = CarOptions().apply {
            routeOptions.alternatives = 3
            avoidanceOptions.avoidTollRoads = false
            optimizationMode = OptimizationMode.FASTEST
        }

        routingEngine.calculateRoute(waypoints, carOptions) { routingError, routes ->
            if (routingError == null && routes?.isNotEmpty() == true) {
                callback(routes[0])
            } else {
                callback(null)
            }
        }
    }
}
```

### 4. CarPlay/Android Auto Integration
```java
// AndroidAutoService.java - Android Auto projection
package com.example.ivi.projection;

import android.content.Intent;
import com.google.android.apps.auto.sdk.CarActivity;

public class AndroidAutoService extends CarActivity {
    @Override
    public void onCreate() {
        super.onCreate();

        // Start Android Auto projection
        Intent intent = new Intent("com.google.android.gms.car.PROJECTION_SERVICE");
        startService(intent);
    }

    @Override
    public void onCarConnectionStateChanged(int state) {
        if (state == CarConnection.STATE_CONNECTED) {
            // Phone connected: mirror Android Auto UI
            enableProjectionMode();
        }
    }
}
```

### 5. Voice Assistant Integration (Alexa/Google Assistant)
```python
# voice_assistant.py - Voice command handler
import speech_recognition as sr
import pyttsx3

class VoiceAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.tts = pyttsx3.init()

    def listen_for_command(self):
        with sr.Microphone() as source:
            print("Listening...")
            audio = self.recognizer.listen(source)

        try:
            command = self.recognizer.recognize_google(audio)
            self.process_command(command)
        except sr.UnknownValueError:
            self.speak("Sorry, I didn't understand that.")

    def process_command(self, command):
        if "navigate to" in command.lower():
            destination = command.lower().replace("navigate to", "").strip()
            self.navigate(destination)
        elif "set temperature" in command.lower():
            temp = int(command.split()[-1])
            self.set_hvac_temperature(temp)

    def speak(self, text):
        self.tts.say(text)
        self.tts.runAndWait()
```

## HMI Framework (Qt QML)
```qml
/* DashboardView.qml - Main instrument cluster */
import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    width: 1920
    height: 720

    // Speedometer
    Item {
        id: speedometer
        x: 100
        y: 100

        Canvas {
            id: speedArc
            width: 400
            height: 400

            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height);

                // Draw arc for speed (0-240 km/h)
                ctx.beginPath();
                ctx.arc(200, 200, 150, 0.75 * Math.PI, (0.75 + 1.5 * (vehicleSpeed / 240)) * Math.PI);
                ctx.lineWidth = 20;
                ctx.strokeStyle = "#00FF00";
                ctx.stroke();
            }

            Connections {
                target: vehicleData
                onSpeedChanged: speedArc.requestPaint()
            }
        }

        Text {
            text: vehicleData.speed + " km/h"
            font.pixelSize: 48
            color: "white"
            anchors.centerIn: parent
        }
    }

    // Battery SOC gauge
    Rectangle {
        x: 600
        y: 100
        width: 300
        height: 50
        color: "transparent"
        border.color: "white"

        Rectangle {
            width: parent.width * (vehicleData.batterySOC / 100)
            height: parent.height
            color: vehicleData.batterySOC > 20 ? "#00FF00" : "#FF0000"
        }

        Text {
            text: vehicleData.batterySOC + "%"
            color: "white"
            anchors.centerIn: parent
        }
    }
}
```

## IVI CAN Interface (DBC)
```
VERSION ""

NS_ :

BS_:

BU_: IVI VCU BCM BMS

/* IVI User Commands */
BO_ 1024 IVI_UserCommand: 8 IVI
 SG_ IVI_DriveMode : 0|8@1+ (0,0) [0|3] ""  VCU
 SG_ IVI_ACTempSet : 8|8@1+ (0.5,10) [10|35] "C"  BCM
 SG_ IVI_ACFanSpeed : 16|8@1+ (0,0) [0|7] ""  BCM

VAL_ 1024 IVI_DriveMode 0 "Eco" 1 "Normal" 2 "Sport" 3 "Custom";
```

## References
- Android Automotive OS Developer Guide
- QNX CAR Platform API Reference
- HERE SDK for Automotive
- CarPlay App Programming Guide
- W3C Automotive Web Platform Specification

## Common Issues
- High CPU usage from rendering complex 3D gauges
- CarPlay/Android Auto disconnection during navigation
- Voice recognition accuracy in noisy cabin
- Slow boot time (> 10 seconds)
