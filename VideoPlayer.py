"""This script plays a video using opencv. It provides features for
viewing the video, such as going back and forth certain frames, 
rescaling the window and displaying debug info.

The user can use keyboard inputs to access these features at runtime.
"""

import os
import sys
import time
import tkinter

import cv2

import VectorClasses as VC


class VideoPlayer:
    """Create and manage video and respond to user input.

    All properties related to the video output are handled by
    this class. It has a reference to the InputManager and the
    TextManager. It has an endless while-loop which only stops
    if the video ends or the user quits (calling quit_video).
    """
    def __init__(self, video_source):
        """Initialise video properties and start update"""
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)
        
        # General video properties.
        self.frame_title = "Video Player"
        self.skipping_time = 3 # In seconds.
        self.current_frame = 0
        self.frames_per_second = int(self.vid.get(cv2.CAP_PROP_FPS))
        # This number is PC specific and is only a temporary solution
        self.milseconds_per_frame = int(428 / self.frames_per_second)
        self.amount_of_frames = int(self.vid.get(cv2.CAP_PROP_FRAME_COUNT))

        if self.milseconds_per_frame < 1:
            raise ValueError("FPS need to be lower", self.frames_per_second)

        # Window size related properties.
        self.monitor_size = self.get_monitor_size()
        self.vid_size = VC.IntVector2(
            int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)), 
            int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
        )
        self.displayed_vid_size = self.vid_size
        self.screen_scale = 0

        # Boolean properties.
        self.is_running = True
        self.is_paused = False
        self.is_fullscreen = False
        self.show_debug_text = False
        self.flip_horizontally = False

        # Class instances.
        self.input_manager = InputManager()
        self.text_manager = TextManager(self)
        # Kick off the update loop.
        self.update()

    def __del__(self):
        """Properly close video and destroy display window."""
        self.is_paused = False
        self.is_running = False

        if self.vid.isOpened():
            self.vid.release()
        cv2.destroyAllWindows()

    def update(self):
        """Update video as long as it has not ended or user has quit.
        
        If the video runs like normal, then update to the next frame
        and check for any user input. If video is paused, just check
        for any user input.
        """
        while self.is_running:
            # Check user input as long as the video is paused.
            while self.is_paused:
                self.input_action(
                    self.input_manager.checkInputs(cv2.waitKey(0)))

            ret, frame = self.get_frame()

            if not ret:
                return
            self.draw_frame(frame)

            # Wait appropriate time and check for any user input.
            k = cv2.waitKey(self.milseconds_per_frame)
            self.input_action(self.input_manager.checkInputs(k))

    def get_monitor_size(self):
        """Return monitor size as an IntVector2"""
        root = tkinter.Tk()
        root.withdraw()

        width, height = root.winfo_screenwidth(), root.winfo_screenheight()
        size = VC.IntVector2(width, height)

        root.destroy()
        return size

    def get_frame(self, frame_to_get=-1):
        """Load the frame frame_to_get (default -1, next frame).
        
        If the video ended, set is_running to False which will
        stop the loop in the update.
        """
        if frame_to_get != -1:
            # Clamp the frame in [0, amount_of_frames].
            frame_to_get = min(max(0, frame_to_get), self.amount_of_frames)
            # Subtract one in order to offset frame correctly.
            self.vid.set(1, frame_to_get - 1)
            self.current_frame = frame_to_get - 1

        ret, frame = self.vid.read()
        self.current_frame += 1

        # If video ended (or something unexpected happend) stop
        # running the video in the update loop.
        if not ret:
            self.is_running = False

        return ret, frame

    def draw_frame(self, frame):
        """Take in the frame to draw and display it in the window"""
        outFrame = cv2.resize(
            frame, (self.displayed_vid_size.x, self.displayed_vid_size.y))

        if self.flip_horizontally:
            outFrame = cv2.flip(outFrame, 1)

        # Only calculate texts if debug should be displayed.
        if self.show_debug_text:
            self.text_manager.putTexts(outFrame)

        cv2.imshow(self.frame_title, outFrame)

    def input_action(self, action):
        """Call action if it is callable"""
        if action == None:
            return

        # In case developer messed up the action, raise error.
        if not callable(action):
            raise ValueError("Given Action is not a callable", action)
        
        action(self)

    def center_video(self):
        """Calculate center position of window based on monitor- and
        display-size and move the windows position.
        """
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
        """Change screen size based on screen_scale."""
        self.is_fullscreen = False

        if self.screen_scale == 0:
            new_size = self.vid_size
        elif self.screen_scale > 0:
            new_size = self.vid_size + 0.25*self.screen_scale * self.vid_size
        elif self.screen_scale < 0:
            new_size = self.vid_size * (0.85 * -1/self.screen_scale)
        
        self.displayed_vid_size = new_size
        # Because the window size changed, re-center the window.
        self.center_video()

    # The Following functions are all referenced by the InputManager.
    def quit_video(self):
        """Quit video by deleting this instance (self)."""
        self.__del__()

    def toggle_pause(self):
        """Toggle between paused and unpaused state."""
        self.is_paused = not self.is_paused

    def skip_forward(self):
        """Skip forward in time by converting the time to frames."""
        _, frame = self.get_frame(
            self.current_frame + self.frames_per_second * self.skipping_time)
        self.draw_frame(frame)

    def skip_backward(self):
        """Skip backward in time by converting the time to frames."""
        _, frame = self.get_frame(
            self.current_frame - self.frames_per_second * self.skipping_time)
        self.draw_frame(frame)

    def skip_one_frame_forward(self):
        """Skip one frame ahead."""
        _, frame = self.get_frame(self.current_frame + 1)
        self.draw_frame(frame)

    def skip_one_frame_backward(self):
        """Skip one frame back."""
        _, frame = self.get_frame(self.current_frame - 1)
        self.draw_frame(frame)

    def toggle_debug(self):
        """Toggle text on/off, update frame in case it's paused."""
        self.show_debug_text = not self.show_debug_text

        _, frame = self.get_frame(self.current_frame)
        self.draw_frame(frame)

    def screen_scale_up(self):
        """Change increase screen size by one."""
        # WARNING: Hard coded number.
        self.screen_scale = min(4, self.screen_scale + 1)
        self.change_screen_size()

        _, frame = self.get_frame(self.current_frame)
        self.draw_frame(frame)

    def screen_scale_down(self):
        """Change decrease screen size by one."""
        # WARNING: Hard coded number.
        self.screen_scale = max(-4, self.screen_scale - 1)
        self.change_screen_size()

        _, frame = self.get_frame(self.current_frame)
        self.draw_frame(frame)
    
    def toggle_fullscreen(self):
        """Toggle fullscreen, fullscreen is realized by 
        rescaling window and not actually going fullscreen."""
        if self.is_fullscreen:
            # If window was fullscreen, then exit it.
            self.change_screen_size()
        else:
            self.is_fullscreen = True
            # Calculate slightly bigger monitor_size for better result.
            self.displayed_vid_size = (
                self.monitor_size
                + VC.IntVector2(self.monitor_size[0] // 64, 0)
            )
            self.center_video()

        _, frame = self.get_frame(self.current_frame)
        self.draw_frame(frame)

    def toggle_flip_image_horizontally(self):
        self.flip_horizontally = not self.flip_horizontally

        _, frame = self.get_frame(self.current_frame)
        self.draw_frame(frame)


class InputManager:
    """Store input relations and references to VideoPlayer functions.
    
    Every input is stored as an Array, with the first element
    acting like a key in a dictionary. A dictionary is not used here
    because every key the user presses gets checked, regardless if
    they have a function associated with them or not.
    The second and third element have debug info for the user, the
    last element contains a reference to the function that gets
    called once the key is pressed.
    """
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
            VideoPlayer.skip_one_frame_forward],
        [109, "M", "Flip image horizontally",
            VideoPlayer.toggle_flip_image_horizontally]
    ]

    def checkInputs(self, input_key):
        """Check if input_key is a viable key, if so,
        return the function corresponding to the key."""
        # In case no key was pressed, return None
        if input_key == -1:
            return None

        print(input_key)

        for input in self.inputs:
            if input[0] == input_key:
                return input[3]
        return None


class TextManager:
    """Manage text that gets put on the video.
    
    The information gets taking from the VideoPlayer and updates
    every time a frame is drawn.
    Putting text on the frame with cv2.putText is very inefficient,
    use as few characters as possible.
    """
    def __init__(self, video_player):
        """Initialise text properties."""
        self.video_player = video_player
        self.texts = []

        # Origin, position of the text starting in top left corner.
        self.org = (25, 40)
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.scale = 0.75
        self.thickness = 2

        self.realFPS = video_player.vid.get(cv2.CAP_PROP_FPS)
        self.maxTime = self.convertTime(
            self.video_player.amount_of_frames // self.realFPS)

    def updateTexts(self):
        """Update texts by reading properties from video_player."""
        curFrame = self.video_player.current_frame
        res = self.video_player.displayed_vid_size
        flip = "H" if self.video_player.flip_horizontally else "-"

        self.texts = [
            "{}/{}".format(
                self.convertTime(curFrame // self.realFPS), self.maxTime),
            "R: {}".format(res),
            "F: {}".format(flip)
        ]

    def putTexts(self, frame):
        """Put everything from texts onto the frame."""
        self.updateTexts()

        # Loop through texts and put it into a single string.
        outText = ""
        for text in self.texts:
            outText += text + "; "
        outText = outText.removesuffix("; ")

        # Put background for better readability.
        cv2.putText(
            frame, outText, self.org, self.font, self.scale, 
            (0, 0, 0), self.thickness * 3, cv2.LINE_AA
        )
        # Put foreground.
        cv2.putText(
            frame, outText, self.org, self.font, self.scale,
            (255, 255, 255), self.thickness, cv2.LINE_AA
        )

    def convertTime(self, seconds):
        """Convert given seconds into a string of min:s and return."""
        return time.strftime("%M:%S", time.gmtime(seconds))


class CommandManager:
    """Handle command prompts from the user if any are given.
    
    Provides the user with the ability to run commands.
    """
    def __init__(self):
        """Initialise commands and the command_symbol."""
        self.command_symbol = "-c"
        # commands store a reference to the function the relate to.
        self.commands = [
            ["help, -h", "Display available commands", 
                CommandManager.help_command],
            ["input, -i", "Display input keys", 
                CommandManager.input_command]
        ]

    def check_commands(self, command_key):
        """Run command corresponding to command_key if valid."""
        validCommand = False

        for command in self.commands:
            # Split required because command is has multiple keys.
            if command_key in command[0].split(", "):
                if not callable(command[2]):
                    raise ValueError("Command not callable", command)
                validCommand = True
                command[2](self)
        
        # If command_key was not found in any command, raise error. 
        if not validCommand:
            raise ValueError(
                "\'{}\' is not a viable command.\n"
                + "Use \'{} help\' to view available comamnds."
                .format(command_key, self.command_symbol)
            )
    
    # The following functions are referenced in commands and called
    # by check_commands.
    def help_command(self):
        """Print all available commands."""
        print("---\nFollowing commands can be used for this script:\n")

        for command in self.commands:
            print("{} - {}".format(command[0], command[1]))

    def input_command(self):
        """Print all available input keys."""
        print("---\nAvailable input keys (shortcuts for the video):\n")

        # Neccassary reference to InputManager. If text file is used
        # instead, then the reference becomes uneccassary.
        IM = InputManager()
        for input in IM.inputs:
            print("{} - {}".format(input[1], input[2]))


if __name__ == "__main__":
    command_manager = CommandManager()

    # No command or video file is given.
    if len(sys.argv) < 2:
        raise ValueError(
            "No video location or command was given.\n"
            + "Use \'{}\' if you want to enter a command."
            .format(command_manager.command_symbol)
        )
    
    # A command is given.
    if sys.argv[1] == command_manager.command_symbol:
        if len(sys.argv) != 3:
            raise ValueError("Need exactly 2 arguments for command.")
        command_manager.check_commands(sys.argv[2])
    # A file is given.
    elif os.path.isfile(sys.argv[1]):
        vPlayer = VideoPlayer(sys.argv[1])
    else:
        raise FileNotFoundError(
            "Did not find specified video file", sys.argv[1])