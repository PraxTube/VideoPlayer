import cv2
import time
import tkinter

class VideoPlayer:
    secondsPerFrame = int(1000 / 60) # maybe change to 65 or 70

    frameTitle = "Video Player"

    def __init__(self, video_source):
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)

        self.inputManager = InputManager()
        self.monitorSize = self.getMonitorSize()
        self.vidSize = (int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)), 
            int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)))

        self.lastFrameTimeStamp = 0

        self.updateFrame()

    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()
        cv2.destroyAllWindows()
    
    def getMonitorSize(self):
        root = tkinter.Tk()
        root.withdraw()
        size = (root.winfo_screenwidth(), root.winfo_screenheight())
        root.destroy()

        return size

    def getNextFrame(self, frameToGet = -1):
        if frameToGet == -1:
            ret, frame = self.vid.read()
            return ret, frame

    def updateFrame(self):
        def getTimeDifference():
            timeDif = self.secondsPerFrame - int(time.time() - self.lastFrameTimeStamp)
            timeDif = max(1, timeDif)
            self.lastFrameTimeStamp = time.time()
            return timeDif
            
        ret, frame = self.getNextFrame()
        
        if not ret:
            return
            
        outFrame = cv2.resize(frame, self.vidSize)
        cv2.imshow(self.frameTitle, outFrame)

        k = cv2.waitKey(getTimeDifference())
        self.inputAction(self.inputManager.checkInputs(k))

        self.updateFrame()

    def inputAction(self, action):
        if action == None:
            return

        if not callable(action):
            raise ValueError("Given Action is not a function", action)
        
        action(self)

    def quitVideo(self):
        self.__del__()

    def centerVideo(self):
        cv2.moveWindow(self.frameTitle, (self.monitorSize[0] // 2) - (self.vidSize[0] // 2), 
            (self.monitorSize[1] // 2) - (self.vidSize[1] // 2))

class InputManager:
    inputs = [  [113, 'q', "Quit video player", VideoPlayer.quitVideo],
                [100, 'd', "Test function", VideoPlayer.centerVideo]]

    def __init__(self):
        pass

    def checkInputs(self, inputKey):
        if inputKey == -1:
            return None

        for input in self.inputs:
            if input[0] == inputKey:
                return input[3]
        return None

videoFile = "C:/Users/lukar/OneDrive/Desktop/kickboxing.mp4"

vPlayer = VideoPlayer(videoFile)
