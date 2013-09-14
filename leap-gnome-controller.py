#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  Leap Motion GNOME Controller
#  Copyright © 2013 Joaquim Rocha <me@joaquimrocha.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import Leap
from Xlib import X, XK
from Xlib.display import Display
from Xlib import display
from Xlib.ext.xtest import fake_input
from gi.repository import Gdk
import sys, time, math
from Leap import CircleGesture, SwipeGesture, KeyTapGesture
import time
import threading



ACTIVITIES_KEY = (XK.XK_Super_L,)
SNAP_LEFT = (XK.XK_Control_L, XK.XK_Super_L, XK.XK_Left)
SNAP_RIGHT = (XK.XK_Control_L, XK.XK_Super_L, XK.XK_Right)
SNAP_MAX = (XK.XK_Control_L, XK.XK_Super_L, XK.XK_Up)
SNAP_MIN = (XK.XK_Control_L, XK.XK_Super_L, XK.XK_Down)
WORKSPACE_UP = (XK.XK_Control_R, XK.XK_Alt_R, XK.XK_Up)
WORKSPACE_DOWN = (XK.XK_Control_R, XK.XK_Alt_R, XK.XK_Down)
MOVE_DESKTOP_BASE_KEY_COMBO = (XK.XK_Meta_L, XK.XK_Control_L)
INCREASE_ZOOM_COMBO = (XK.XK_Control_L, XK.XK_plus)
DECREASE_ZOOM_COMBO = (XK.XK_Control_L, XK.XK_minus)
SWITCHER = (XK.XK_Super_L, XK.XK_W)
TAB = XK.XK_Tab
RIGHT = XK.XK_Right
LEFT = XK.XK_Left
UP = XK.XK_Up
DOWN = XK.XK_Down
ALT = XK.XK_Alt_L

class FuncThread(threading.Thread):
    def __init__(self, target, *args):
        self._target = target
        self._args = args
        threading.Thread.__init__(self)
 
    def run(self):
        self._target(*self._args)

class EventManager(object):

    POINTER_MIN_MOVE = 2.0 # px
    ZOOM_THRESHOLD = 10 # mm
    ZOOM_FUNCTION_DURATION = .5 # seconds
    ZOOM_FUNCTION_RESET_TIMEOUT = 2 # seconds
    FUNCTIONS_DEFAULT_DURATION = .5 # seconds

    def __init__(self):
        self._display = Display()
        self._run_times = {}
        self._last_pointer_move = 0
        self._last_zoom = 0
        self._last_zoom_distance = -1
	self.s = self._display.screen()
	self.root = self.s.root

    def scroll_up(self):
        self._press_and_release_key_combo(WORKSPACE_UP)

    def scroll_down(self):
        self._press_and_release_key_combo(WORKSPACE_DOWN)

    def _set_pointer(self, x, y):
        self.root.warp_pointer(x,y)
	self._display.sync()

    def click(self):
        fake_input(self._display, X.ButtonPress, 1)
        fake_input(self._display, X.ButtonRelease, 1)
        self._display.sync()

    def mouse_press(self):
        fake_input(self._display, X.ButtonPress, 1)
        self._display.sync()

    def mouse_release(self):
        fake_input(self._display, X.ButtonRelease, 1)
        self._display.sync()

    def toggle_activities(self):
        self._run_function(self._toggle_activities_real,
                           self.FUNCTIONS_DEFAULT_DURATION)

    def _toggle_activities_real(self):
        self._press_and_release_key_combo(ACTIVITIES_KEY)

    def _run_function(self, function, timeout, *args):
        '''
        Runs a function if it hasn't run for less than the
        specified timeout.
        '''
        last_run = self._run_times.get(function, 0)
        current_time = time.time()
        if current_time - last_run > timeout:
            function(*args)
        self._run_times[function] = current_time

    def _move_desktop(self, dir_keysym):
        self._press_and_release_key_combo(MOVE_DESKTOP_BASE_KEY_COMBO +
                                          (dir_keysym,))

    def move_next_desktop(self):
        self._run_function(self._move_desktop, self.FUNCTIONS_DEFAULT_DURATION,
                           XK.XK_Down)

    def move_previous_desktop(self):
        self._run_function(self._move_desktop, self.FUNCTIONS_DEFAULT_DURATION,
                           XK.XK_Up)

    def _press_and_release_key_combo(self, combo):
        for action in (X.KeyPress, X.KeyRelease):
            for keysym in combo:
                key = self._display.keysym_to_keycode(keysym)
                fake_input(self._display, action, key)
            self._display.sync()

    def _press_and_release_key(self, akey):
        for action in (X.KeyPress, X.KeyRelease):
            key = self._display.keysym_to_keycode(akey)
            fake_input(self._display, action, key)
            self._display.sync()

    def _press_key(self, akey):
    	key = self._display.keysym_to_keycode(akey)
    	fake_input(self._display, X.KeyPress, key)
        self._display.sync()

    def _release_key(self, akey):
    	key = self._display.keysym_to_keycode(akey)
    	fake_input(self._display, X.KeyRelease, key)
        self._display.sync()

    def _change_zoom(self, distance):
        if distance > self._last_zoom_distance:
            self._press_and_release_key_combo(INCREASE_ZOOM_COMBO)
        else:
            self._press_and_release_key_combo(DECREASE_ZOOM_COMBO)

    def zoom(self, distance):
        '''
        Uses the distance between two points to check whether the zoom
        should be increased, decreased or not applied at all.
        '''
        current_time = time.time()
        time_since_last_zoom = current_time - self._last_zoom
        if time_since_last_zoom < self.ZOOM_FUNCTION_DURATION:
            return
        if time_since_last_zoom > self.ZOOM_FUNCTION_RESET_TIMEOUT:
            self._last_zoom_distance = -1
        if self._last_zoom_distance == -1:
            self._last_zoom_distance = distance
        elif abs(self._last_zoom_distance - distance) > self.ZOOM_THRESHOLD:
            self._change_zoom(distance)
            self._last_zoom_distance = distance
        self._last_zoom = current_time

    def zoom_scroll(self, distance):
        '''
        Uses the distance between two points to check whether the zoom
        should be increased, decreased or not applied at all.
        '''
        current_time = time.time()
        time_since_last_zoom = current_time - self._last_zoom
        if time_since_last_zoom < self.ZOOM_FUNCTION_DURATION:
            return
        if time_since_last_zoom > self.ZOOM_FUNCTION_RESET_TIMEOUT:
            self._last_zoom_distance = -1
        if self._last_zoom_distance == -1:
            self._last_zoom_distance = distance
        elif abs(self._last_zoom_distance - distance) > self.ZOOM_THRESHOLD:
            if self._last_zoom_distance - distance > 0:
		self._press_and_release_key(LEFT)
	    else:
		self._press_and_release_key(RIGHT)
        self._last_zoom = current_time

class ControllerListener(Leap.Listener):

    MIN_CIRCLE_RADIUS = 40.0
    MIN_SWIPE_LENGTH = 120.0
    ENABLED_GESTURES = [Leap.Gesture.TYPE_CIRCLE,
                        Leap.Gesture.TYPE_SCREEN_TAP,
                        Leap.Gesture.TYPE_KEY_TAP,
                        Leap.Gesture.TYPE_SWIPE]
    last_num_fingers = 1
    last_event = 0
    CLICK_TIMEOUT = 400.
    disable = False
    THUMB_THRESH = 0.85
    SWIPE_THRESH = 450.
    HAND_THRESH = 650.
    SWIPE_Y_THRESH = .7
    SWITCH_THRESH = 290.
    is_in_switch_mode = False
    is_pressed = False
    POINTER_X_THRESH = 0.36
    VELOCITY_THRESH = 200.
    alt_down = False
    SNAP_RANGE = 20.
    
    DEPTH = 1000.
    HEIGHT = 400.
    WIDTH = 1000.

    def __init__(self):
        Leap.Listener.__init__(self)
        screen = Gdk.Screen.get_default()
        self._event_manager = EventManager()
        self._screen_width = screen.get_width()
        self._screen_height = screen.get_height()

    def on_connect(self, controller):
        if controller.config.set('Gesture.Circle.MinArc', 2 * Leap.PI) and \
           controller.config.set('Gesture.Circle.MinRadius', self.MIN_CIRCLE_RADIUS) and \
           controller.config.set('Gesture.Swipe.MinLength', self.MIN_SWIPE_LENGTH):
            controller.config.save()

        for gesture in self.ENABLED_GESTURES:
            controller.enable_gesture(gesture)

    def handle_two_hands(self, frame):
        if self.alt_down:
	    self.alt_down = False
	    self._event_manager._release_key(ALT)
	    self._event_manager.mouse_release()
		    
    def dot(self, u, w):
        return u.x * w.x + u.y * w.y + u.z * w.z
    
    def mag(self, u):
        return math.sqrt(u.x * u.x + u.y * u.y + u.z * u.z)

# from http://stackoverflow.com/questions/5666222/3d-line-plane-intersection
    def add_v3v3(self, a, b):
	return [a[0] + b[0],
		    a[1] + b[1],
		    a[2] + b[2]]


    def sub_v3v3(self, a, b):
	return [a[0] - b[0],
		    a[1] - b[1],
		    a[2] - b[2]]


    def dot_v3v3(self, a, b):
	return (a[0] * b[0] +
		    a[1] * b[1] +
		    a[2] * b[2])

    def mul_v3_fl(self, a, f):
	a[0] *= f
	a[1] *= f
	a[2] *= f

# intersection function
    def isect_line_plane_v3(self, p0, p1, p_co, p_no, epsilon=0.00001):
        """
        p0, p1: define the line
        p_co, p_no: define the plane, p_no need not be normalized.
   
        return a Vector or None if the intersection can't be found.
        """
 
        u = self.sub_v3v3(p1, p0)
        w = self.sub_v3v3(p0, p_co)
        dot = self.dot_v3v3(p_no, u)

        #if abs(dot) > epsilon:
            # the factor of the point between p0 -> p1 (0 - 1)
            # if 'fac' is between (0 - 1) the point intersects with the segment.
            # otherwise:
            #  < 0.0: behind p0.
            #  > 1.0: infront of p1.
        fac = -self.dot_v3v3(p_no, w) / dot
        self.mul_v3_fl(u, fac)
        return self.add_v3v3(p0, u)
        #else:
            # The segment is parallel to plane
         #   return None

#end from http://stackoverflow.com/questions/5666222/3d-line-plane-intersection

    def thumb(self, fingers):
	if (fingers.frontmost == fingers.leftmost):
	    return False
	if (fingers.leftmost.direction.x > 0):
	    return False
	if abs(self.dot(fingers.leftmost.direction, fingers.rightmost.direction)) > self.THUMB_THRESH:
	    return False
	return True

    def move_mouse_from_finger(self, finger):
	try:
	    location =  self.isect_line_plane_v3(finger.tip_position, self.add_v3v3(finger.tip_position, finger.direction), [0., 0., -self.DEPTH], [0.,0.,self.DEPTH])
	    x = location[0] + self._screen_width/2. + self.WIDTH
	    y = -location[1] + self._screen_height/2. + self.HEIGHT
	    if x > self._screen_width:
	        x = self._screen_width
	    if abs (x - self._screen_width/2) < self.SNAP_RANGE:
	        if x - self._screen_width/2 > 0:
	    	    x = self._screen_width/2 + 2
	        else:
		    x = self._screen_width/2 - 2
	    if x < 0:
	        x = 0
	    if y < 0:
	        y = 0
	    if y > self._screen_height:
	        y = self._screen_height
	    self._event_manager._set_pointer(x, y)
	    if self.alt_down and ((x == self._screen_width or x == self._screen_width / 2 - 2 or x == self._screen_width / 2 + 2 or x == 0) or (y == 0)):
	        self.alt_down = False
	        self._event_manager._release_key(ALT)
	        self._event_manager.mouse_release()
	    elif self.alt_down and y == self._screen_height:
	        self.alt_down = False
	        self._event_manager._release_key(ALT)
	        self._event_manager.mouse_release()
	        self._event_manager._press_and_release_key_combo(SNAP_MIN)
	except:
	    pass
    def handle_one_hand(self, frame):
	
	if (len(frame.hands.frontmost.fingers) <= 2) and self.is_in_switch_mode and not self.thumb(frame.hands.frontmost.fingers):
	    self.move_mouse_from_finger(frame.hands.frontmost.fingers.frontmost)
	elif len(frame.hands.frontmost.fingers) <= 3:
	    millis = int(round(time.time() * 1000))
	    if (self.is_in_switch_mode) and millis - self.last_event > self.SWIPE_THRESH:
		self.move_mouse_from_finger(frame.hands.frontmost.fingers.frontmost)
		self.last_event = millis
		self._event_manager.click()
		self.is_in_switch_mode = False
	    elif millis - self.last_event > self.SWIPE_THRESH:
            	for gesture in frame.gestures():
	            if gesture.type == Leap.Gesture.TYPE_SWIPE:
                        self.last_event = millis
                        swipe = SwipeGesture(gesture)
		        mag_z = abs(swipe.direction.z)
		        mag_x = abs(swipe.direction.x)
                        mag_y = abs(swipe.direction.y)
		        if (mag_z > mag_x) and (mag_z > mag_y):
			    return
                        if (mag_x >= mag_y):
                            if (swipe.direction.x < 0):
                                self._event_manager._press_and_release_key_combo(SNAP_LEFT)
                            else:
	                        self._event_manager._press_and_release_key_combo(SNAP_RIGHT)
                        else:
                            if (swipe.direction.y > 0):
                                self._event_manager._press_and_release_key_combo(SNAP_MAX)
                            else:
	                        self._event_manager._press_and_release_key_combo(SNAP_MIN)
			return
	elif len(frame.hands.frontmost.fingers) > 4:
	    millis = int(round(time.time() * 1000))
	    if millis - self.last_event > self.HAND_THRESH and (not self.is_in_switch_mode):
		self.is_in_switch_mode = True
	        self._event_manager._press_and_release_key_combo(SWITCHER)
	    self.last_event = millis

        elif len(frame.hands.frontmost.fingers) >= 4 and not (self.is_in_switch_mode):
            millis = int(round(time.time() * 1000))
            had_gesture = False
	    for gesture in frame.gestures():
	        if gesture.type == Leap.Gesture.TYPE_SWIPE and millis - self.last_event > self.HAND_THRESH:
		    self.last_event = millis
		    had_gesture = True
                    swipe = SwipeGesture(gesture)
		    if abs(swipe.direction.y) < self.SWIPE_Y_THRESH:
			return
                    if swipe.direction.y > 0:
		        self._event_manager.scroll_up()
		    else:
			self._event_manager.scroll_down()
		    return
	    #if not had_gesture:
	    #    self._event_manager.toggle_activities()           

    def on_frame(self, controller):
        frame = controller.frame()
	
        if frame.hands.empty:
	    if (self.is_in_switch_mode):
	        self._event_manager._press_and_release_key_combo(SWITCHER)
	        self.is_in_switch_mode = False
            return

        if len(frame.hands) > 1:
            self.handle_two_hands(frame)
            return

        self.handle_one_hand(frame)

def main():
    listener = ControllerListener()
    controller = Leap.Controller()

    controller.add_listener(listener)
    sys.stdin.readline()
    controller.remove_listener(listener)

if __name__ == "__main__":
    main()
