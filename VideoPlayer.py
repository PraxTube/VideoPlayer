""" This script plays a video using opencv. It provides features for
viewing the video, such as skipping by a single frame, rescaling view
and displaying debug info."""

import os
import sys
import time
import tkinter

import cv2

import VectorClasses as VC


class VideoPlayer:
    frame_title = "Video Player"
    skipping_time = 3 # in seconds

    def __init__(self, video_source):
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)
        
        self.frames_per_second = int(self.vid.get(cv2.CAP_PROP_FPS))
        self.milseconds_per_frame = int(428 / self.frames_per_second)
        self.amount_of_frames = int(self.vid.get(cv2.CAP_PROP_FRAME_COUNT))

        if self.milseconds_per_frame < 1:
            raise ValueError("FPS need to be lower", self.frames_per_second)

        self.monitor_size = self.get_monitor_size()
        self.vid_size = VC.IntVector2(
            int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)), 
            int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
        )
        self.displayed_vid_size = self.vid_size

        self.current_frame = 0
        self.screen_scale = 0

        self.is_running = True
        self.is_paused = False
        self.is_fullscreen = False
        self.showDebugText = False

        self.input_manager = InputManager()
        self.text_manager = TextManager(self)

        self.update()

    def __del__(self):
        self.is_paused = False
        self.is_running = False

        if self.vid.isOpened():
            self.vid.release()
        cv2.destroyAllWindows()

    def update(self):
        while self.is_running:
            while self.is_paused:
                self.input_action(
                    self.input_manager.checkInputs(cv2.waitKey(0))
                )

            ret, frame = self.get_frame()

            if not ret:
                return
            self.draw_frame(frame)

            k = cv2.waitKey(self.milseconds_per_frame)
            self.input_action(self.input_manager.checkInputs(k))

    def get_monitor_size(self):
        root = tkinter.Tk()
        root.withdraw()

        width, height = root.winfo_screenwidth(), root.winfo_screenheight()
        size = VC.IntVector2(width, height)

        root.destroy()
        return size

    def get_frame(self, frameToGet = -1):
        if frameToGet != -1:
            frameToGet = min(max(0, frameToGet), self.amount_of_frames) # frameToGet in [0, amount_of_frames
            self.vid.set(1, frameToGet - 1)
            self.current_frame = frameToGet - 1

        ret, frame = self.vid.read()
        self.current_frame += 1

        if not ret:
            self.is_running = False

        return ret, frame

    def draw_frame(self, frame):
        outFrame = cv2.resize(
            frame, (self.displayed_vid_size.x, self.displayed_vid_size.y)
        )

        if self.showDebugText:
            self.text_manager.putTexts(outFrame)

        cv2.imshow(self.frame_title, outFrame)

    def input_action(self, action):
        if action == None:
            return

        if not callable(action):
            raise ValueError("Given Action is not a callable", action)
        
        action(self)

    def center_video(self):
        new_width = (
            (self.monitor_size[0] // 2)
            - (self.displayed_vid_size[0] // 2)
        )

        new_height = (
            (self.monitor_size[1] // 2)
            - (self.displayed_vid_size[1] // 2)
        )

        cv2.moveWindow(self.frame_title, new_width, new_height)

    def change_screen_size(self):
        self.is_fullscreen = False

        if self.screen_scale == 0:
            new_size = self.vid_size
        elif self.screen_scale > 0:
            new_size = self.vid_size + 0.25*self.screen_scale * self.vid_size
        elif self.screen_scale < 0:
            new_size = self.vid_size * (0.85 * -1/self.screen_scale)
        
        self.displayed_vid_size = new_size
        self.center_video()

    # --- Input Functions
    def quit_video(self):
        self.__del__()

    def toggle_pause(self):
        self.is_paused = not self.is_paused

    def skip_forward(self):
        _, frame = self.get_frame(
            self.current_frame + self.frames_per_second * self.skipping_time
        )
        self.draw_frame(frame)

    def skip_backward(self):
        _, frame = self.get_frame(
            self.current_frame - self.frames_per_second * self.skipping_time
        )
        self.draw_frame(frame)

    def skip_one_frame_forward(self):
        _, frame = self.get_frame(self.current_frame + 1)
        self.draw_frame(frame)

    def skip_one_frame_backward(self):
        _, frame = self.get_frame(self.current_frame - 1)
        self.draw_frame(frame)

    def toggle_debug(self):
        self.showDebugText = not self.showDebugText

        _, frame = self.get_frame(self.current_frame)
        self.draw_frame(frame)

    def screen_scale_up(self):
        self.screen_scale = min(4, self.screen_scale + 1)
        self.change_screen_size()

        _, frame = self.get_frame(self.current_frame)
        self.draw_frame(frame)

    def screen_scale_down(self):
        self.screen_scale = max(-4, self.screen_scale - 1)
        self.change_screen_size()

        _, frame = self.get_frame(self.current_frame)
        self.draw_frame(frame)
    
    def toggle_fullscreen(self):
        if self.is_fullscreen:
            self.change_screen_size()
        else:
            self.is_fullscreen = True
            self.displayed_vid_size = (
                self.monitor_size
                + VC.IntVector2(self.monitor_size[0] // 64, 0)
            )
            self.center_video()

        _, frame = self.get_frame(self.current_frame)
        self.draw_frame(frame)
    # --- END Input Functions


class InputManager:
    inputs = [
        [113, "Q", "Quit video player", 
            VideoPlayer.quit_video],
        [97, "A", "Skip backward", 
            VideoPlayer.skip_backward],
        [100, "D", "Skip forward", 
            VideoPlayer.skip_forward],
        [114, "R", "Scale Screen-size up", 
            VideoPlayer.screen_scale_up],
        [116, "T", "Scale Screen-size down", 
            VideoPlayer.screen_scale_down],
        [102, "F", "Enter and Exit Fullscreen", 
            VideoPlayer.toggle_fullscreen],
        [104, "H", "Hide or show Debug Info", 
            VideoPlayer.toggle_debug],
        [32, "SPACE", "Pause video", 
            VideoPlayer.toggle_pause],
        [65, "LSHIFT + A", "Skip one frame backward", 
            VideoPlayer.skip_one_frame_backward],
        [68, "LSHIFT + D", "Skip one frame forward", 
            VideoPlayer.skip_one_frame_forward]
    ]

    def checkInputs(self, input_key):
        if input_key == -1:
            return None

        for input in self.inputs:
            if input[0] == input_key:
                return input[3]
        return None


class TextManager:
    def __init__(self, video_player):
        self.video_player = video_player
        self.texts = []

        self.org = (25, 40)
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.scale = 0.75
        self.thickness = 2

        self.textSpacing = VC.IntVector2(0, 60)

        self.realFPS = video_player.vid.get(cv2.CAP_PROP_FPS)
        self.maxTime = self.convertTime(
            self.video_player.amount_of_frames // self.realFPS
        )

        self.updateTexts()

    def updateTexts(self):
        curFrame = self.video_player.current_frame
        res = self.video_player.displayed_vid_size

        self.texts = [  
            "{}/{}".format(
                self.convertTime(curFrame // self.realFPS), self.maxTime
            ),
            "R: {}".format(res)
        ]

    def putTexts(self, frame):
        self.updateTexts()

        outText = ""
        for text in self.texts:
            outText += text + "; "
        outText = outText.removesuffix("; ")

        cv2.putText(
            frame, outText, self.org, self.font, self.scale, 
            (0, 0, 0), self.thickness * 3, cv2.LINE_AA
        )
        cv2.putText(
            frame, outText, self.org, self.font, self.scale,
            (255, 255, 255), self.thickness, cv2.LINE_AA
        )

    def convertTime(self, seconds):
        return time.strftime("%M:%S", time.gmtime(seconds))


class CommandManager:
    def __init__(self):
        self.command_symbol = "-c"
        self.commands = [
            ["help, -h", "Display available commands", 
                CommandManager.help_command],
            ["input, -i", "Display input keys", 
                CommandManager.input_command]
        ]

    def check_commands(self, commandKey):
        validCommand = False

        for command in self.commands:
            if commandKey in command[0].split(", "):
                if not callable(command[2]):
                    raise ValueError("Command not callable", command)
                validCommand = True
                command[2](self)
        
        if not validCommand:
            raise ValueError(
                "\'{}\' is not a viable command.\n"
                + "Use \'{} help\' to view available comamnds."
                .format(commandKey, self.command_symbol)
            )
    
    # --- Commands
    def help_command(self):
        print("---\nFollowing commands can be used for this script:\n")

        for command in self.commands:
            print("{} - {}".format(command[0], command[1]))

    def input_command(self):
        print("---\nAvailable input keys (shortcuts for the video):\n")

        IM = InputManager()
        for input in IM.inputs:
            print("{} - {}".format(input[1], input[2]))
    # --- END Commands


if __name__ == "__main__":
    command_manager = CommandManager()

    if len(sys.argv) < 2:
        raise ValueError(
            "No video location or command was given.\n"
            + "Use \'{}\' if you want to enter a command."
            .format(command_manager.command_symbol)
        )
    
    if sys.argv[1] == command_manager.command_symbol:
        if len(sys.argv) != 3:
            raise ValueError("Need exactly 2 arguments for command.")
        command_manager.check_commands(sys.argv[2])
    elif os.path.isfile(sys.argv[1]):
        vPlayer = VideoPlayer(sys.argv[1])
    else:
        raise FileNotFoundError(
            "Did not find specified video file", sys.argv[1]
        )