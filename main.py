#!/usr/bin/env python3

import os, sys, pygame, json
from pygame import *
from datetime import datetime
from ctypes import c_char_p

try:
    from multiprocessing import Value, Process, Condition, Array, Manager
except ImportError:
    from processing import Value,  Process,  Condition


from settings import *
from pyo_sound import mixer_loops

from loop import Loop, LoopSync
from sections import Section

HOME_DIR = os.path.dirname(os.path.abspath(__file__))


def get_personal_settings():
    """Get Personal settings from file"""
    with open(os.path.join(HOME_DIR,'settings/personal.json'), 'r') as file:
        text = file.read()
        objects = json.loads(text)
        print(objects)
        return objects
        

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
    manager = Manager()
    mixer_list_loops = manager.dict()
    mixer = Process( target = mixer_loops, 
                    args = (mixer_event,
                            mixer_channel,
                            mixer_metro_time, 
                            mixer_tick, 
                            mixer_duration, 
                            mixer_list_loops)
                    ).start()
    
    print('Main')
    
    pers_settings = get_personal_settings()
    dur_loops = pers_settings['dur_loops']
    
    pygame.mouse.set_cursor(*pygame.cursors.arrow)
    for row in range(0, COUNT_ROWS):
        #print('row ', row)
        margin_row += MARGIN
        margin_sect += row * MARGIN*0.5
        loops = []
        margin_loop = 0
        for col in range(0, COUNT_IN_ROW):
            margin_loop += MARGIN 
            x = LOOP_RAD + 2 * col * LOOP_RAD + margin_loop + TOTAL_X_MARGIN
            y = LOOP_RAD + 2 * row * LOOP_RAD + margin_row + TOTAL_Y_MARGIN
            loop = Loop(LOOP_RAD, 
                        int(x), int(y), 
                        mixer_channel, 
                        mixer_event, 
                        mixer_tick, 
                        mixer_duration, 
                        dur_loops, 
                        )
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
                            loops, 
                            mixer_channel, 
                            mixer_event,
                            mixer_metro_time, 
                            mixer_tick, 
                            total_dict_loops
                            )
    main_process(screen, bg, list_loops, 
                total_dict_loops, 
                loop_sync, 
                timer, 
                mixer_tick, 
                mixer_list_loops)
    mixer_event.value = QUIT
    pygame.quit()
    if mixer:
        mixer.join()
    return 'Quit!'
 

def main_process(screen, bg, list_loops, 
                total_dict_loops, 
                loop_sync, 
                timer, 
                mixer_tick, 
                mixer_list_loops):
    loop_in_focus = 1
    #waiting = False
    current_sect = 1
    prev_sect = None
    done = False
    loop_for_rec = 1
    id_loop_after_rec = 0
    all_tick_checked = True
    #time_click = None
    
    while not done:  # main circle
        e_loop = 1000
        KEY = None
        key_for_focus = 0
        mouse_pos = pygame.mouse.get_pos()
        for e in pygame.event.get():  # events
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.dict['button'] == 4:
                    e_loop = WHEEL_UP
                    if pygame.key.get_pressed()[pygame.K_z]:
                        e_loop = LENGTH_INC
                elif e.dict['button'] == 5:
                    e_loop = WHEEL_DOWN
                    if pygame.key.get_pressed()[pygame.K_z]:
                        e_loop = LENGTH_DEC
                elif e.dict['button'] == 1:
                    e_loop = CLICK
                    key_for_focus = 1
            # Keyboard
            if e.type == KEYDOWN:
                KEY = e.key
                print(KEY)
                if KEY == METRO_STOP_PLAY_KEY:
                    loop_sync.start_stop()
                elif KEY == ERASE_KEY:
                    e_loop = ERASE_ALL
                    loop_in_focus = 1
                    current_sect = 1
                elif KEY == ERASE_LAST_LOOP_KEY:
                    e_loop = ERASE
                elif KEY == MUTE_KEY:
                    e_loop = MUTE_ALL
                elif KEY == K_UP:
                    e_loop = WHEEL_UP
                elif KEY == K_DOWN:
                    e_loop = WHEEL_DOWN
                elif KEY == QUIT_KEY:
                    done = True
                elif KEY == REC_PLAY_LOOP_KEY:
                    e_loop = REC_PLAY_LOOP
                elif KEY == TOGGLE_SECTION_KEY:
                    e_loop = TOGGLE_SECTION
                elif KEY == SELECT_SECTION_KEY:
                    e_loop = SELECT_SECTION
            if e.type == pygame.QUIT:
                done = True
        screen.blit(bg, (0,0)) 
        loop_sync.event(e_loop, mouse_pos, total_dict_loops)
        loop_sync.draw(screen)
        #
        # Work with sections and Loops
        #
        if e_loop == SELECT_SECTION:
            if current_sect == COUNT_ROWS:
                current_sect = 1
                prev_sect = COUNT_ROWS
            else:
                prev_sect = current_sect
                current_sect += 1
                
        elif e_loop == TOGGLE_SECTION:
            next_prev_sect = current_sect
            if prev_sect and current_sect != prev_sect:
                current_sect = prev_sect
            prev_sect = next_prev_sect
            
        if len(list_loops[current_sect-1][0].loops) > 0:
            id_loop_after_rec = list_loops[current_sect-1][0].loops[-1].id
        else:
            id_loop_after_rec = COUNT_IN_ROW * (current_sect - 1)
        
        # Mute other section while record loop from current section
        if e_loop == REC_PLAY_LOOP or e_loop == TOGGLE_SECTION:
            #print("LIST_LOOPS: ", len(list_loops))
            for item in list_loops:
                section = item[0]
                #print('section.loops: ', section.loops)
                for loop in section.loops:
                    mixer_list_loops[loop.id] = section.focus
                    if section.focus:
                        loop.unmute_show()
                        section.muted = False
                    else:
                        loop.mute_show()
                        section.muted = True
                
        for l in list_loops:
            sect = l[0]
            loops = l[1]
            #
            # Section Events
            #
            last_loop_ob = sect.check_focus(current_sect)
            
            if sect.prev:
                prev_sect = sect.id
            
            if sect.focus:
                if not last_loop_ob:
                    loop_in_focus = loops[0].id
                else:
                    loop_in_focus = last_loop_ob.id+1
            if e_loop == ERASE:
                if sect.focus and sect.playing:
                    loop_for_erase = sect.loops.pop()
                    mixer_list_loops.pop(loop_for_erase.id, None)
                    loop_for_erase.event(ERASE)
                    if len(sect.loops) > 0: 
                        id_loop_after_rec = sect.loops[-1].id
                    else:
                        id_loop_after_rec = COUNT_IN_ROW * (sect.id - 1)
                    if id_loop_after_rec == 1 and not sect.loops:
                        loop_for_rec = 1
                    
            #        
            # Loops Events
            #       
            for loop in loops:
                
                loop.check_focus(key_for_focus, mouse_pos, loop_in_focus)
                loop.next_for_rec(loop_for_rec)
                
                if e_loop != ERASE:
                    
                    loop.event(e_loop, mouse_pos, sect.focus, loop_for_rec)
                    if e_loop == REC_PLAY_LOOP:
                        if loop.has_sound and loop.id == loop_for_rec:
                            id_loop_after_rec = loop.id
                            sect.loops.append(loop)
                            #print('added loop:', )
                            #print('len loops: ', len(sect.loops))
                    
                        
                loop.draw(screen)
                if not loop.tick_checked:
                    all_tick_checked = False
            
            sect.draw(screen)
            
        if e_loop == ERASE_ALL:
            for item in list_loops:
                section = item[0]
                for loop in section.loops:
                    mixer_list_loops.pop(loop.id, None)
                section.loops = []
            loop_for_rec = 1
            loop_in_focus = 1
                
        loop_sync.check_started()    
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

