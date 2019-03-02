#!/usr/bin/env python3

import sys, pygame
from pygame import *

try:
    from multiprocessing import Value, Process, Condition
except ImportError:
    from processing import Value,  Process,  Condition


from settings import *
from pyo_sound import mixer_loops

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
    mixer = Process( target = mixer_loops, 
                    args = (mixer_event,
                            mixer_channel, )
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
                        mixer_event)
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
                            mixer_event
                            )
    main_process(screen, bg,  list_loops, total_dict_loops, loop_sync, timer)
    mixer_event.value = QUIT
    pygame.quit()
    return 'Quit!'
 

def main_process(screen, bg,  list_loops, total_dict_loops, loop_sync, timer):
    loop_in_focus = 1
    waiting = False
    current_sect = 1
    prev_sect = None
    done = False
    
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
                    e_loop = CLICK
                    key_for_focus = 1
            # Keyboard
            if e.type == KEYDOWN:
                KEY = e.key
                print(KEY)
                if KEY == REC_PLAY_SYNC_KEY:
                    loop_sync.start_stop()
                if KEY == SELECT_SECTION_KEY:
                    if current_sect == COUNT_ROWS:
                        current_sect = 1
                    else:
                        current_sect += 1
                if KEY == ERASE_KEY:
                    e_loop=ERASE
                    loop_in_focus = 1
                    current_sect = 1
                if KEY == MUTE_KEY:
                    e_loop=MUTE
                if KEY == K_UP:
                    e_loop = WHEEL_UP
                if KEY == K_DOWN:
                    e_loop = WHEEL_DOWN
                if KEY == QUIT_KEY:
                    done = True
                    
            if e.type == pygame.QUIT:
                done = True
        screen.blit(bg, (0,0)) 
        loop_sync.play_sound()
        delta = loop_sync.delta
        time_sync = loop_sync.time_sync
        loop_sync.event(e_loop, mouse_pos)
        loop_sync.draw(screen)
        for dict in list_loops:
            sect = dict[0]
            loops = dict[1]
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
                    loop_in_focus = sect.loops[-1].id
            for loop in loops:
                loop.check_focus(key_for_focus, mouse_pos, loop_in_focus)
                #print('check focus: ', loop.id)
                if loop.focus:
                    #print('loop in focuse: ',  loop.id)
                    (loop_in_focus, 
                    waiting, 
                    stop_prev_event, 
                    start_curr_event) = rec_play_logik(KEY,
                                                     loop,
                                                     total_dict_loops,
                                                     delta,
                                                     waiting,
                                                     sect,
                                                     prev_sect)
                if sect.focus and start_curr_event:
                    loop.event(PLAY, mouse_pos)
                if sect.prev and stop_prev_event and sect.playing:
                    loop.event(STOP_PLAY, mouse_pos)
                else:
                    loop.event(e_loop, mouse_pos)
                #loop.play_sound(delta, time_sync)
                loop.draw(screen)
            sect.draw(screen)
        pygame.display.update()     # update all views
        timer.tick(MAIN_TICK)
    print('Good buy!')
    
    return True
 

def rec_play_logik(key, loop, loops, delta, waiting, sect, prev_sect):

    loop = loops[loop.id]
    loop_in_focus = loop.id
    next_loop = loops[loop.id+1]
    stop_prev_event = False
    start_curr_event = False
    if  key == REC_PLAY_LOOP_KEY:
        if delta < 0:
            waiting = True
    if loop.recording:
        if waiting and delta >= 0:
            loop.event(STOP_RECORD)
            next_loop.focus = True
            loop_in_focus = next_loop.id
            sect.loops.append(loop)
            waiting = False
    elif loop.playing:
        if delta >= 0:
            next_loop.event(RECORD)
            waiting = False
    else:
        if waiting and delta >= 0:
            
            loop.event(RECORD)
            if prev_sect:
                stop_prev_event = True
            if sect.loops and not sect.playing:
                start_curr_event = True

            waiting = False
    return loop_in_focus, waiting, stop_prev_event, start_curr_event


#if __name__ == "__main__":
res = main()
print(res)

