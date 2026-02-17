#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "lncdtask",
#     "psychopy-visionscience",
# ]
#
# [tool.uv.sources]
# lncdtask = { git = "https://github.com/LabNeuroCogDevel/lncdtask" }
# ///

import argparse
import sys
import psychopy
import lncdtask
from lncdtask.lncdtask import LNCDTask, RunDialog, FileLogger, ExternalCom, create_window
import pandas as pd
import numpy as np
from grasp_trcount import HandGrasp, args_to_settings
import psychopy.visual.radial

STIM_PER_SEC=1/10 #: flip checkers every 10 Hz
CHECKER_SIZE=.2 #: size of single checker rectangle. (fullsreen=2)
REST_TEXT = "Relax"  #: text displayed during rest/relax block
ON_TEXT = "Grid"  #: text displayed in make a fist block
BLOCK_ORDER = (ON_TEXT, REST_TEXT)  #: sequence
DEFAULT_NTRIAL = 1  #: number of rest+graps pairs. NTRIAL of each.
DEFAULT_NTR = 4  #: number of counted pulses per individual block
#: NB. VESO sequence has pulse for VESO and BOLD. 2 pulses per repetition
TRIGGERS = [
    "equal"
]  #: what key advances the get ready screen? TTL to key via button box


def draw_checkers(rect, offset=0, size=CHECKER_SIZE):
    # -1,-1 is left, bottom. x is first, left<->right
    for i, x in enumerate(np.arange(-1-size/2, 1, size*2)):
        for y in np.arange(-1+size/2, 1, size*2):
            rect.pos = (x+offset*size, y)
            rect.draw()
            rect.pos = (x+size+offset*size, y+size)
            rect.draw()
class Checkers(HandGrasp):
    """
    Extending HandGrasp (LNCDTask) to display checkerboard.
    """

    def __init__(self, *karg, **kargs):
        super().__init__(*karg, **kargs)

        # for checkers
        self.rect = psychopy.visual.Rect(self.win, size=(.2, .2), fillColor="white")

        # for annotating trial info
        self.annote = psychopy.visual.TextStim(self.win, text="", name="annotation")
        self.annote.setColor([-0.8, -0.8, -0.8], "rgb")
        self.annote.pos = (0.5, -0.8)  # center-right, bottom of screen

        self.block_i = 0
        self.tr_times = [0, 0]
        self.block_trs = 0
        self.block_label = BLOCK_ORDER[0]
        self.start_pulse_time = 0

        #grating_res = 256
        #self.stim = psychopy.visual.RadialStim(win=self.win, units="pix", size=(grating_res, grating_res))

    def draw_annote(self):
        self.annote.text = f"{self.block_trs}@{self.block_i}={self.block_label} {self.tr_times[0]:0.3f} {self.tr_times[1]:0.3f}"
        self.annote.draw()
        self.msgbox.draw()

    def record_event(self, flip_time):
            self.add_event(
                onset=flip_time,
                event_name=self.block_label,
                start_time=self.start_pulse_time)



def main(settings):
    """
    Run the task.
    @param settings dict of parameters from args_to_settings
    """

    #: dialog's already up if seen, so dont provide option to toggle
    #: logging disableing is only for testing. dont provide option for that (only in CLI params)
    tweakable = {k: v for k,v in settings.items() if k not in ['no_dialog', 'logging']}
    run_info = RunDialog(
        # ntrials should be nblocks
        extra_dict=tweakable, order=["subjid", "ntrials", "ntr","annotate", "instructions", "fullscreen"]
    )

    if settings.get("no_dialog"):
        pass # use whatever defaults we were given
    elif not run_info.dlg_ok():
        return False

    # pull in new settings
    # make sure types are as expected after editing (as string)
    settings = run_info.info
    settings["ntrials"] = int(settings["ntrials"])
    settings["ntr"] = int(settings["ntr"])

    # and get a participant object for saving files
    participant = run_info.mk_participant(["checkers"])

    # onset_df is typically precomputed.
    # kludge: will popoulate as we go so output csv file still has data for GLM
    #         but timing will be determined dynamically/at run time by TR pulses
    empty_df = pd.DataFrame({"onset": [], "event_name": [], "onset0": []})

    win = None # let lncdtask figure it out
    if not settings['fullscreen']:
        win = create_window(False)
    hc = Checkers(onset_df=empty_df, win=win)

    # escape quits
    hc.gobal_quit_key()

    # record timing to file and to standard out
    if settings.get("logging"):
        logger = FileLogger()
        logger.new(participant.log_path("grasp"))
        hc.externals.append(logger)  # save events "marked" to a file
    hc.externals.append(ExternalCom())  # and print to terminal

    # instructins include specific generated information:
    # how long an and how many trials
    instructions = [
        lambda: hc.instruction("This is the checkers task!"),
    ]

    # if no instructions request, just show the last one
    if settings["instructions"]:
        hc.run_instructions(instructions)

    # track two TR times. likely BOLD volume and then VASO volume
    tr_times = [0, 0]
    # wait for scanner trigger.
    # This is pulse is recieved precieding the first volume that's collected
    hc.start_pulse_time = hc.get_ready()
    prev_tr = hc.start_pulse_time # for TR calc. only on first 2 trs
    hc.mark_external(f"STARTING: recieved first TR pulse {hc.start_pulse_time}")
    stim_i = 0
    last_flip = hc.start_pulse_time

    # BUG? why does 'waiting for scanner' text need to be cleared?
    hc.msgbox.text = ""
    hc.msgbox.draw()

    while hc.block_i/len(BLOCK_ORDER) < settings["ntrials"]:
        # flip screen at sim rate
        now = psychopy.core.getTime()
        if hc.block_label != REST_TEXT and now - last_flip >= STIM_PER_SEC:
            draw_checkers(hc.rect, stim_i%2)
            stim_i += 1

            if settings.get("annotate"):
                hc.draw_annote()

            hc.win.flip()
            last_flip = psychopy.core.getTime()

        elif hc.block_label == REST_TEXT:
            hc.msgbox.text = REST_TEXT
            hc.msgbox.height = 0.5
            hc.msgbox.setColor([1, 1, 1], "rgb") # white
            hc.msgbox.draw()
            if settings.get("annotate"):
                hc.draw_annote()
            hc.win.flip()
            last_flip = psychopy.core.getTime()
        else:
            # checkers but not time for checkboard flip
            pass

        if hc.block_trs == 0:
            hc.record_event(last_flip)


        # track TR recieved
        keys = psychopy.event.getKeys(keyList=TRIGGERS)
        if keys:
            if hc.tr_times[1] == 0:
                hc.tr_times[hc.block_trs % 2] = now - prev_tr
            prev_tr = now
            hc.mark_external(f"pulse {now - hc.start_pulse_time:-0.3f} ({now})")
            hc.block_trs += 1
            if hc.block_trs > settings["ntr"]:
                hc.block_trs = 0
                hc.block_i += 1
                hc.block_label = BLOCK_ORDER[hc.block_i % len(BLOCK_ORDER)]

    psychopy.core.wait(tr_times[1]) # wait for last volume to acquire
    hc.finished("Done!\nThank you!")

    # save complete event info.
    if settings.get("logging"):
        hc.onset_df.to_csv(
            participant.run_path(f"grasp_tr1-{tr_times[0]:0.3f}_tr2-{tr_times[1]:0.3f}")
        )


if __name__ == "__main__":

    settings = args_to_settings(sys.argv[1:])
    main(settings)
