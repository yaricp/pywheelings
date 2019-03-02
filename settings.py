#Record setings
ALSA_RECORD_SYSTEM = 0
PORTAUDIO_RECORD_SYSTEM = 1
JACK_RECORD_SYSTEM = 2
#CURRENT_RECORD_SYSTEM = JACK_RECORD_SYSTEM
#CURRENT_RECORD_SYSTEM = PORTAUDIO_RECORD_SYSTEM
CURRENT_RECORD_SYSTEM = ALSA_RECORD_SYSTEM

# main properties of view

WIN_WIDTH = 800                     # width of main window
WIN_HEIGHT = 640                    # hight of main window
DISPLAY = (WIN_WIDTH, WIN_HEIGHT)   # width and height of main window
BACKGROUND_COLOR = "#0F010F"
COUNT_IN_ROW = 6                    # count of loop in line
COUNT_ROWS = 3                      # count of rows of loops
LOOP_RAD  = 50                      # radius of main circle of loop
MARGIN = 10                         # margins between of loops
TOTAL_X_MARGIN = 50
TOTAL_Y_MARGIN = 50

# view of sections
COLOR_SECT = (0, 0, 255)
FOCUS_COLOR_SECT = (100, 205, 255)
PREV_COLOR_SECT = (5, 145, 255)
THICKNESS_LINE_SECT = 1
FOCUS_THICKNESS_LINE_SECT = 3

# view of loops

COLOR_LOOP = (0, 0, 255)
COLOR_VOL_LOOP = (0, 255, 255)
NORMAL_VALUE_LOOP = 0.7
STEP_VALUE_LOOP = 0.01
THICKNESS_LINE_LOOP = 1
FOCUS_THICKNESS_LINE_LOOP = 3
COLOR_FONT_LOOP = [255, 255, 255]
SIZE_FONT_LOOP = 25
TYPE_FONT_LOOP = None
# for Sync loop
LOOP_RAD_SYNC = LOOP_RAD+10
COLOR_LOOP_SYNC = (0, 0, 255)
COLOR_VOL_LOOP_SYNC = (0, 255, 255)
NORMAL_VALUE_LOOP_SYNC = 0.05
STEP_VALUE_LOOP_SYNC = 0.01
THICKNESS_LINE_LOOP_SYNC = 1
FOCUS_THICKNESS_LINE_LOOP_SYNC = 3

# Evevnts of mouse

WHEEL_UP = 12
WHEEL_DOWN = 13
CLICK = 11

# Keys for main events of looper

MUTE_KEY = 32   #Space key
REC_PLAY_LOOP_KEY = 99      #key C
ERASE_LAST_LOOP_KEY = 122     #key Z
REC_PLAY_SYNC_KEY = 98      #key B
SELECT_SECTION_KEY = 118     #key V
TOGGLE_SECTION_KEY = 120     #key X
ERASE_KEY =113  #key Q

# Events of loops

PLAY = 0
STOP_PLAY = 1
STOP_PLAY_ALL = 2
STOP_RECORD = 3
RECORD = 4
ERASE = 5
ERASE_ALL = 6
MUTE = 7
UNMUTE = 8
MUTE_ALL = 9
UNMUTE_ALL = 10
QUIT = 20

# Other properties
NEW_LOOP = 255
CORRECT_TIME_SYNC = 3
MAIN_TICK = 1000
REC_FILE_EXT = 'wav'
PLAY_FILE_EXT = 'wav'
PATH_FILES = 'files/'
SOUND_SYNC_LOOP = 'high.wav'
#Aqua
#	
#
#(  0, 255, 255)
#
#Black
#	
#
#(  0,   0,   0)
#
#Blue
#	
#
#(  0,  0, 255)
#
#Fuchsia
#	
#
#(255,   0, 255)
#
#Gray
#	
#
#(128, 128, 128)
#
#Green
#	
#
#(  0, 128,   0)
#
#Lime
#	
#
#(  0, 255,   0)
#
#Maroon
#	
#
#(128,  0,   0)
#
#Navy Blue
#	
#
#(  0,  0, 128)
#
#Olive
#	
#
#(128, 128,   0)
#
#Purple
#	
#
#(128,  0, 128)
#
#Red
#	
#
#(255,   0,   0)
#
#Silver
#	
#
#(192, 192, 192)
#
#Teal
#	
#
#(  0, 128, 128)
#
#White
#	
#
#(255, 255, 255)
#
#Yellow
#	
#
#(255, 255,   0)
