#!/usr/bin/env python3

import sys, pygame
from pygame import *
from datetime import datetime

try:
    from multiprocessing import Value, Process, Condition
except ImportError:
    from processing import Value,  Process,  Condition


from settings import *
from pyo_sound import mixer_loops
from utils import *

from loop import Loop, LoopSync
from sections import Section



def main():
    pygame.mixer.init(44100,  -16, 2, 1024)
    
    pygame.init()
    screen = pygame.display.set_mode(DISPLAY)
    pygame.display.set_caption("py Wheels")
    bg = Surface((WIN_WIDTH,WIN_HEIGHT))
    bg.fill(Color(BACKGROUND_COLOR))
    timer = pygame.time.Clock()
    margin_row = 0
    margin_sect = MARGIN * 0.5
    list_loops = []
    total_dict_loops = {}
    mixer_event = Value('i', 1000)
    mixer_channel = Value('i', 0)
    mixer_metro_time = Value('d', DEFAULT_METRO_TIME)
    mixer_duration = Value('d', DEFAULT_LOOP_LENGTH)
    mixer_tick = Value('i', 0)
    mixer_time_tick = Value('d', 0)
    mixer = Process( target = mixer_loops, 
                    args = (mixer_event,
                            mixer_channel,
                            mixer_metro_time, 
                            mixer_tick, 
                            mixer_duration
                           )
                    ).start()
    
    print('Main')
    
    pygame.mouse.set_cursor(*pygame.cursors.diamond)
    for row in range(0, COUNT_ROWS):
        #print('row ', row)
        margin_row += MARGIN
        margin_sect += row * MARGIN*0.5
        loops = []
        margin_loop = 0
        for col in range(0, COUNT_IN_ROW):
            #print('col ',  col)
            margin_loop += MARGIN 
            x = LOOP_RAD + 2 * col * LOOP_RAD + margin_loop + TOTAL_X_MARGIN
            y = LOOP_RAD + 2 * row * LOOP_RAD + margin_row + TOTAL_Y_MARGIN
            loop = Loop(LOOP_RAD, 
                        int(x), int(y), 
                        mixer_channel, 
                        mixer_event, 
                        mixer_metro_time, 
                        mixer_tick, 
                        mixer_duration)
            total_dict_loops.update({loop.id: loop})
            loops.append(loop)
        
        height = (2 * LOOP_RAD)+MARGIN
        y = row * height + MARGIN * 0.5 + TOTAL_Y_MARGIN
        width = (2 * LOOP_RAD*COUNT_IN_ROW)+(MARGIN * (COUNT_IN_ROW+1))
        sect = Section(TOTAL_X_MARGIN, y, width, height)
        list_loops.append([sect, loops])
    loop_sync = LoopSync(   LOOP_RAD_SYNC,
                            int(TOTAL_X_MARGIN+(width/2)),
                            int(MARGIN+height*COUNT_ROWS+LOOP_RAD_SYNC+TOTAL_Y_MARGIN),
                            mixer_channel, 
                            mixer_event,
                            mixer_metro_time, 
                            mixer_tick
                            )
    main_process(screen, bg,  list_loops, 
                total_dict_loops, loop_sync, 
                timer, mixer_tick)
    mixer_event.value = QUIT
    pygame.quit()
    if mixer:
        mixer.join()
    return 'Quit!'
 

def main_process(screen, bg,  
                list_loops,
                total_dict_loops, 
                loop_sync, 
                timer, 
                mixer_tick):
    loop_in_focus = 1
    waiting = False
    current_sect = 1
    prev_sect = None
    done = False
    loop_for_rec = 1
    id_loop_after_rec = 0
    all_tick_checked = True
    time_click = None
    
    while not done:  # main circle
        e_loop = 1000
        KEY = None
        key_for_focus = 0
        #Mouse moving
        
        mouse_pos = pygame.mouse.get_pos()
        for e in pygame.event.get():  # events
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.dict['button'] == 4:
                    e_loop = WHEEL_UP
                elif e.dict['button'] == 5:
                    e_loop = WHEEL_DOWN
                elif e.dict['button'] == 1:
#                    and check_time_clicked(time_click):
#                    time_click = datetime.now()
                    e_loop = CLICK
                    key_for_focus = 1
            # Keyboard
            if e.type == KEYDOWN:
                KEY = e.key
                print(KEY)
                if KEY == METRO_STOP_PLAY_KEY:
                    loop_sync.start_stop()
                if KEY == SELECT_SECTION_KEY:
                    if current_sect == COUNT_ROWS:
                        current_sect = 1
                    else:
                        current_sect += 1
                    if len(list_loops[current_sect-1][0].loops) > 0:
                        id_loop_after_rec = list_loops[current_sect-1][0].loops[-1].id
                    else:
                        id_loop_after_rec = COUNT_IN_ROW * (current_sect - 1)
                if KEY == ERASE_KEY:
                    e_loop=ERASE
                    loop_in_focus = 1
                    current_sect = 1
                if KEY == MUTE_KEY:
                    e_loop = MUTE
                if KEY == K_UP:
                    e_loop = WHEEL_UP
                if KEY == K_DOWN:
                    e_loop = WHEEL_DOWN
                if KEY == QUIT_KEY:
                    done = True
                    
            if e.type == pygame.QUIT:
                done = True
        screen.blit(bg, (0,0)) 
        loop_sync.event(e_loop, mouse_pos)
        loop_sync.draw(screen)
        #
        # Work with sections and Loops
        #
        for dict in list_loops:
            sect = dict[0]
            loops = dict[1]
            #
            # Section Events
            #
            if KEY == TOGGLE_SECTION_KEY:
                if prev_sect and current_sect != prev_sect:
                    current_sect = prev_sect
                if sect.playing:
                    e_loop = STOP_PLAY
                elif sect.focus:
                    e_loop = PLAY
            last_loop_ob = sect.check_focus(current_sect)
            if sect.prev:
                prev_sect = sect.id
            if KEY == ERASE_KEY:
                sect.loops = []
            if sect.focus:
                if not last_loop_ob:
                    loop_in_focus = loops[0].id
                else:
                    loop_in_focus = last_loop_ob.id+1
            if KEY == ERASE_LAST_LOOP_KEY:
                if sect.focus and sect.playing:
                    loop_for_erase = sect.loops.pop()
                    loop_for_erase.event(ERASE)
                    if len(sect.loops) > 0: 
                        id_loop_after_rec = sect.loops[-1].id
                    else:
                        id_loop_after_rec = COUNT_IN_ROW * (sect.id - 1)
            #        
            # Loops Events
            #       
            for loop in loops:
                
                loop.check_focus(key_for_focus, mouse_pos, loop_in_focus)
                loop.next_for_rec(loop_for_rec)
                #print('check focus: ', loop.id)
                if loop.id == loop_for_rec and KEY == REC_PLAY_LOOP_KEY:
                    loop.event(REC_PLAY_LOOP_KEY)
                    if loop.has_sound:
                        id_loop_after_rec = loop.id
                        sect.loops.append(loop)
#                if loop.focus:
#                    loop.event(e_loop, mouse_pos)
#                if sect.prev and stop_prev_event and sect.playing:
#                    loop.event(STOP_PLAY, mouse_pos)
#                else:
                loop.event(e_loop, mouse_pos)
                loop.draw(screen)
                if not loop.tick_checked:
                    all_tick_checked = False
            sect.draw(screen)
        if all_tick_checked:
            mixer_tick.value = 0
        for loop in total_dict_loops.values():
            loop.tick_checked = False
        all_tick_checked = True
        loop_for_rec = id_loop_after_rec + 1
        loop_in_focus = id_loop_after_rec
        pygame.display.update()     # update all views
        timer.tick(MAIN_TICK)
    print('Good buy!')
    return True


if __name__ == "__main__":
    res = main()
    print(res)
    sys.exit(0)

