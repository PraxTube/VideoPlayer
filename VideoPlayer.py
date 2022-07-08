import cv2
import sys
import time
import tkinter

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
        self.vidSize = (int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)), 
            int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)))

        self.lastFrameTimeStamp = 0
        self.currentFrame = 0
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
        timeDif = self.milSecondsPerFrame - int(time.time() - self.lastFrameTimeStamp)

        self.lastFrameTimeStamp = time.time()
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
        outFrame = cv2.resize(frame, (1280, 720))

        if self.showDebugText:
            outFrame = self.textManager.putTexts(outFrame)

        cv2.imshow(self.frameTitle, outFrame)

    def inputAction(self, action):
        if action == None:
            return

        if not callable(action):
            raise ValueError("Given Action is not a callable", action)
        
        action(self)

    def centerVideo(self):
        cv2.moveWindow(self.frameTitle, (self.monitorSize[0] // 2) - (self.vidSize[0] // 2), 
            (self.monitorSize[1] // 2) - (self.vidSize[1] // 2))

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
    # --- END Input Functions

class InputManager:
    inputs = [  [113, "Q", "Quit video player", VideoPlayer.quitVideo],
                [32, "SPACE", "Pause video", VideoPlayer.togglePauseVideo],
                [97, "A", "Skip backward", VideoPlayer.skipBackward],
                [100, "D", "Skip forward", VideoPlayer.skipForward],
                [65, "LSHIFT + A", "Skip one frame backward", VideoPlayer.skipOneFrameBackward],
                [68, "LSHIFT + D", "Skip one frame forward", VideoPlayer.skipOneFrameForward],
                [104, "H", "Hide or show Debug Info", VideoPlayer.toggleDebugText]]

    def checkInputs(self, inputKey):
        if inputKey == -1:
            return None
        
        for input in self.inputs:
            if input[0] == inputKey:
                return input[3]
        return None

class TextManager:
    def __init__(self, videoPlayer):
        self.videoPlayer = videoPlayer
        self.texts = []

        self.org = (50, 50)
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.scale = 1
        self.thickness = 2

        self.realFPS = videoPlayer.vid.get(cv2.CAP_PROP_FPS)
        self.maxTime = self.convertTime(self.videoPlayer.amountOfFrames // self.realFPS)

        self.updateTexts()

    def updateTexts(self):
        curFrame = self.videoPlayer.currentFrame
        maxFrame = self.videoPlayer.amountOfFrames
        fps = self.videoPlayer.framesPerSecond

        self.texts = [  "FPS: {}".format(fps),
                        "{}/{}  {}%".format(self.convertTime(curFrame // self.realFPS), self.maxTime, curFrame * 100 // maxFrame)]

    def putText(self, frame, text, org, color, thickness):
        frame = cv2.putText(frame, text, 
            org, self.font, self.scale, color, thickness, cv2.LINE_AA)
        return frame

    def putTexts(self, frame):
        self.updateTexts()

        for i in range(len(self.texts)):
            org = (self.org[0], self.org[1] + 60 * self.scale * i)
            frame = self.putText(frame, self.texts[i], org, (0, 0, 0), self.thickness * 3)
            frame = self.putText(frame, self.texts[i], org, (255, 255, 255), self.thickness)
        return frame

    def convertTime(self, seconds):
        return time.strftime("%H:%M:%S", time.gmtime(seconds))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        videoFile = "./Videos/kickboxing.mp4"
    else:
        videoFile = sys.argv[1]

    vPlayer = VideoPlayer(videoFile)
