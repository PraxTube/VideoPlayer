import cv2
import sys
import time
import tkinter

import VectorClasses as VC

start = 0

class VideoPlayer:
    framesPerSecond = 60
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
        self.isZoomed = False
        self.isFullscreen = False
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
        end = time.time()
        print(time.strftime("Runtime: %M:%S", time.gmtime(end - start)))

    def update(self):
        while self.isRunning:
            while self.isPaused:
                self.inputAction(self.inputManager.checkInputs(cv2.waitKey(0)))

            ret, frame = self.getFrame()

            if not ret:
                return
            self.drawFrame(frame)

            k = cv2.waitKey(self.milSecondsPerFrame)
            self.inputAction(self.inputManager.checkInputs(k))

    def getMonitorSize(self):
        root = tkinter.Tk()
        root.withdraw()
        size = VC.IntVector2(root.winfo_screenwidth(), root.winfo_screenheight())
        root.destroy()

        return size

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

        if self.isZoomed:
            outFrame = outFrame[300:500, 300:500]
            self.centerVideo()

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
        self.isFullscreen = False

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
    
    def toggleFullscreen(self):
        if self.isFullscreen:
            self.changeScreenSize()
        else:
            self.displayedVidSize = self.monitorSize + VC.IntVector2(self.monitorSize[0] // 64, 0)
            self.centerVideo()
            self.isFullscreen = True

        _, frame = self.getFrame(self.currentFrame)
        self.drawFrame(frame)

    def toggleZoom(self):
        self.isZoomed = not self.isZoomed
    # --- END Input Functions

class InputManager:
    inputs = [  [113, "Q", "Quit video player", VideoPlayer.quitVideo],
                [32, "SPACE", "Pause video", VideoPlayer.togglePauseVideo],
                [97, "A", "Skip backward", VideoPlayer.skipBackward],
                [100, "D", "Skip forward", VideoPlayer.skipForward],
                [65, "LSHIFT + A", "Skip one frame backward", VideoPlayer.skipOneFrameBackward],
                [68, "LSHIFT + D", "Skip one frame forward", VideoPlayer.skipOneFrameForward],
                [114, "R", "Scale Screen-size up", VideoPlayer.screenScaleUp],
                [116, "T", "Scale Screen-size down", VideoPlayer.screenScaleDown],
                [122, "Z", "Toggle Zoom Mode", VideoPlayer.toggleZoom],
                [102, "F", "Enter and Exit Fullscreen", VideoPlayer.toggleFullscreen],
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
        vP = self.videoPlayer
        curFrame = vP.currentFrame
        res = vP.monitorSize if vP.isFullscreen else vP.displayedVidSize

        self.texts = [  "{}/{}".format(self.convertTime(curFrame // self.realFPS), self.maxTime),
                        "R: {}".format(res)]

    def putTexts(self, frame):
        self.updateTexts()

        outText = ""
        for text in self.texts:
            outText += text + "; "
        outText = outText.removesuffix("; ")

        cv2.putText(frame, outText, self.org, self.font, self.scale, (0, 0, 0), self.thickness * 3, cv2.LINE_AA)
        cv2.putText(frame, outText, self.org, self.font, self.scale, (255, 255, 255), self.thickness, cv2.LINE_AA)

    def convertTime(self, seconds):
        return time.strftime("%M:%S", time.gmtime(seconds))

if __name__ == "__main__":
    start = time.time()

    if len(sys.argv) < 2:
        videoFile = "./Videos/minSurfaces.mp4"
    else:
        videoFile = sys.argv[1]

    vPlayer = VideoPlayer(videoFile)
