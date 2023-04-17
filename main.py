# main.py -- put your code here!
# EPITA / Majeure Sante / IoT / Lab 02

import machine
import time
import ssd1306
import random
from pyb import ADC, Pin, Timer
import uasyncio as asyncio
import utime
from machine import Timer

i2c = machine.I2C(scl=machine.Pin('A1'), sda=machine.Pin('A8'), freq=100000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
sw=pyb.Switch()

WIDTH = 128
HEIGHT = 32

HEART = [
[ 0, 0, 0, 0, 0, 0, 0, 0, 0],
[ 0, 1, 1, 0, 0, 0, 1, 1, 0],
[ 1, 1, 1, 1, 0, 1, 1, 1, 1],
[ 1, 1, 1, 1, 1, 1, 1, 1, 1],
[ 1, 1, 1, 1, 1, 1, 1, 1, 1],
[ 0, 1, 1, 1, 1, 1, 1, 1, 0],
[ 0, 0, 1, 1, 1, 1, 1, 0, 0],
[ 0, 0, 0, 1, 1, 1, 0, 0, 0],
[ 0, 0, 0, 0, 1, 0, 0, 0, 0],
]

def setupSensor() :
    machine.Pin('B8', machine.Pin.OUT).low()
    machine.Pin('B9', machine.Pin.OUT).high()
    machine.Pin('A0', machine.Pin.IN)


oled.fill(0)
rtc = machine.RTC()
rtc.datetime((2023, 1, 8, 2, 12, 00, 30, 0))

setupSensor()

led = pyb.LED(1)
adc = ADC(Pin('A0'))
MAX_HISTORY = 250
TOTAL_BEATS = 30

last_y = 0

def refresh(bpm, beat, v, minima, maxima):
    global last_y

    oled.vline(0, 0, 32, 0)
    oled.scroll(-1,0) # Scroll left 1 pixel

    if maxima-minima > 0:
        # Draw beat line.
        y = 32 - int(16 * (v-minima) / (maxima-minima))
        oled.line(125, last_y, 126, y, 1)
        last_y = y

    # Clear top text area.
    oled.fill_rect(0,0,128,16,0) # Clear the top text area

    if bpm:
        oled.text("%d" % bpm, 12, 0)

    # Draw heart if beating.
    if beat:
        for y, row in enumerate(HEART):
            for x, c in enumerate(row):
                oled.pixel(x, y, c)

    oled.text(str(rtc.datetime()[4]) + ':' + str(rtc.datetime()[5]) + ':' + str(rtc.datetime()[6]), 50, 0)

    oled.show()

def calculate_bpm(beats):
    if beats:
        beat_time = beats[-1] - beats[0]
        if beat_time:
            beat = (len(beats) / (beat_time)) * 60
            return beat

def detect():
    # Maintain a log of previous values to
    # determine min, max and threshold.
    history = []
    beats = []
    beat = False
    bpm = None

    # Clear screen to start.
    oled.fill(0)

    while True:
        if (sw()) :
            break

        v = adc.read()
        print(v)
        history.append(v)

        # Get the tail, up to MAX_HISTORY length
        history = history[-MAX_HISTORY:]

        minima, maxima = min(history), max(history)

        threshold_on = (minima + maxima * 3) // 4   # 3/4
        threshold_off = (minima + maxima) // 2      # 1/2

        if v > threshold_on and beat == False:
            beat = True
            beats.append(time.time())
            # Truncate beats queue to max
            beats = beats[-TOTAL_BEATS:]
            bpm = calculate_bpm(beats)

        if v < threshold_off and beat == True:
            beat = False

        #print(v, threshold_on, threshold_off)

        refresh(bpm, beat, v, minima, maxima)

def pressed(timer, start_time):
    timer.deinit()
    oled.fill(0)
    reaction_time = utime.ticks_diff(utime.ticks_ms(), start_time)
    oled.text("Reaction time: ", 0, 0)
    oled.text(str(reaction_time) + " ms", 0, 10)
    if (reaction_time < 200) :
        oled.text("Tu es le fast !", 0, 20)
    oled.show()
    time.sleep(5)

def game():
        oled.fill(0)
        oled.text("Press btn when", 0, 0)
        oled.text("symbol appears", 0, 10)
        oled.show()
        
        utime.sleep(random.randint(3, 10))
        
        oled.fill(0)
        oled.text("Symbol", 40, 20)
        oled.show()
        
        start_time = utime.ticks_ms()
        tim = Timer(-1)
        tim.init(period=150)
        
        while sw.value() == False:
            utime.sleep(0.01)

        pressed(tim, start_time)

while True:
    if sw(): 
        game()
    else:
        detect()



