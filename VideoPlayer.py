import cv2
import sys
import time
import tkinter

import VectorClasses as VC

class VideoPlayer:
    framesPerSecond = 24
    milSecondsPerFrame = int(1000 / framesPerSecond)

    frameTitle = "Video Player"
    skipTime = 3 # in seconds

    def __init__(self, video_source):
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)
        
        if self.milSecondsPerFrame < 1:
            raise ValueError("FPS cannot be higher then 1000", self.milSecondsPerFrame)

        self.amountOfFrames = int(self.vid.get(cv2.CAP_PROP_FRAME_COUNT))

        self.monitorSize = self.getMonitorSize()
        self.vidSize = VC.IntVector2(int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)), 
            int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        self.displayedVidSize = self.vidSize

        self.lastFrameTimeStamp = 0
        self.timeDif = 0
        self.currentFrame = 0
        self.screenScale = 0

        self.isRunning = True
        self.isPaused = False
        self.showDebugText = False

        self.inputManager = InputManager()
        self.textManager = TextManager(self)

        self.update()

    def __del__(self):
        self.isPaused = False
        self.isRunning = False

        if self.vid.isOpened():
            self.vid.release()
        cv2.destroyAllWindows()

    def update(self):
        while self.isRunning:
            while self.isPaused:
                self.inputAction(self.inputManager.checkInputs(cv2.waitKey(0)))

            ret, frame = self.getFrame()

            if not ret:
                return
            self.drawFrame(frame)

            k = cv2.waitKey(self.getTimeDifference())
            self.inputAction(self.inputManager.checkInputs(k))

    def getMonitorSize(self):
        # Note: there might be problems when having a multi screen setup, there are fixes however
        # https://stackoverflow.com/questions/3129322/how-do-i-get-monitor-resolution-in-python
        root = tkinter.Tk()
        root.withdraw()
        size = (root.winfo_screenwidth(), root.winfo_screenheight())
        root.destroy()

        return size

    def getTimeDifference(self):
        timeDif = self.milSecondsPerFrame - int((time.time() - self.lastFrameTimeStamp) * 1000)

        self.lastFrameTimeStamp = time.time()
        self.timeDif = timeDif
        print(timeDif)
        return max(1, timeDif)

    def getFrame(self, frameToGet = -1):
        if frameToGet != -1:
            frameToGet = min(max(0, frameToGet), self.amountOfFrames) # frameToGet in [0, amountOfFrames]
            self.vid.set(1, frameToGet - 1)
            self.currentFrame = frameToGet - 1

        ret, frame = self.vid.read()
        self.currentFrame += 1

        if not ret:
            self.isRunning = False

        return ret, frame

    def drawFrame(self, frame):
        outFrame = cv2.resize(frame, (self.displayedVidSize.x, self.displayedVidSize.y))

        if self.showDebugText:
            self.textManager.putTexts(outFrame)

        cv2.imshow(self.frameTitle, outFrame)

    def inputAction(self, action):
        if action == None:
            return

        if not callable(action):
            raise ValueError("Given Action is not a callable", action)
        
        action(self)

    def centerVideo(self):
        cv2.moveWindow(self.frameTitle, (self.monitorSize[0] // 2) - (self.displayedVidSize[0] // 2), 
            (self.monitorSize[1] // 2) - (self.displayedVidSize[1] // 2))

    def changeScreenSize(self):
        if self.screenScale == 0:
            self.displayedVidSize = self.vidSize

        if self.screenScale > 0:
            self.displayedVidSize = self.vidSize + 0.25 * self.screenScale * self.vidSize
        elif self.screenScale < 0:
            self.displayedVidSize = self.vidSize * (0.85 * -1 / self.screenScale)
        
        self.centerVideo()

    # --- Input Functions
    def quitVideo(self):
        self.__del__()

    def togglePauseVideo(self):
        self.isPaused = not self.isPaused

    def skipForward(self): # HARD CODED NUMBER
        _, frame = self.getFrame(self.currentFrame + 24 * self.skipTime)
        self.drawFrame(frame)

    def skipBackward(self): # HARD CODED NUMBER
        _, frame = self.getFrame(self.currentFrame - 24 * self.skipTime)
        self.drawFrame(frame)

    def skipOneFrameForward(self):
        _, frame = self.getFrame(self.currentFrame + 1)
        self.drawFrame(frame)

    def skipOneFrameBackward(self):
        _, frame = self.getFrame(self.currentFrame - 1)
        self.drawFrame(frame)

    def toggleDebugText(self):
        self.showDebugText = not self.showDebugText

        _, frame = self.getFrame(self.currentFrame)
        self.drawFrame(frame)

    def screenScaleUp(self):
        self.screenScale = min(4, self.screenScale + 1)
        self.changeScreenSize()

        _, frame = self.getFrame(self.currentFrame)
        self.drawFrame(frame)

    def screenScaleDown(self):
        self.screenScale = max(-4, self.screenScale - 1)
        self.changeScreenSize()

        _, frame = self.getFrame(self.currentFrame)
        self.drawFrame(frame)
    # --- END Input Functions

class InputManager:
    inputs = [  [113, "Q", "Quit video player", VideoPlayer.quitVideo],
                [32, "SPACE", "Pause video", VideoPlayer.togglePauseVideo],
                [97, "A", "Skip backward", VideoPlayer.skipBackward],
                [100, "D", "Skip forward", VideoPlayer.skipForward],
                [65, "LSHIFT + A", "Skip one frame backward", VideoPlayer.skipOneFrameBackward],
                [68, "LSHIFT + D", "Skip one frame forward", VideoPlayer.skipOneFrameForward],
                [114, "R", "Scale Screen-size up", VideoPlayer.screenScaleUp],
                [102, "F", "Scale Screen-size down", VideoPlayer.screenScaleDown],
                [104, "H", "Hide or show Debug Info", VideoPlayer.toggleDebugText]]

    def checkInputs(self, inputKey):
        if inputKey == -1:
            return None

        print(inputKey)
        
        for input in self.inputs:
            if input[0] == inputKey:
                return input[3]
        return None

class TextManager:
    def __init__(self, videoPlayer):
        self.videoPlayer = videoPlayer
        self.texts = []

        self.org = (25, 40)
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.scale = 0.75
        self.thickness = 2

        self.textSpacing = VC.IntVector2(0, 60)

        self.realFPS = videoPlayer.vid.get(cv2.CAP_PROP_FPS)
        self.maxTime = self.convertTime(self.videoPlayer.amountOfFrames // self.realFPS)

        self.updateTexts()

    def updateTexts(self):
        curFrame = self.videoPlayer.currentFrame

        self.texts = [  "{}/{}".format(self.convertTime(curFrame // self.realFPS), self.maxTime),
                        "R: {}".format(self.videoPlayer.displayedVidSize),
                        "t: {}".format(self.videoPlayer.timeDif)]

    def putTexts(self, frame):
        self.updateTexts()

        outText = ""
        for text in self.texts:
            outText += text + "; "
        outText = outText.removesuffix("; ")

        outText *= self.videoPlayer.screenScale

        cv2.putText(frame, outText, self.org, self.font, self.scale, (0, 0, 0), self.thickness * 3, cv2.LINE_AA)
        cv2.putText(frame, outText, self.org, self.font, self.scale, (255, 255, 255), self.thickness, cv2.LINE_AA)

    def convertTime(self, seconds):
        return time.strftime("%M:%S", time.gmtime(seconds))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        videoFile = "./Videos/kickboxing.mp4"
    else:
        videoFile = sys.argv[1]

    vPlayer = VideoPlayer(videoFile)
