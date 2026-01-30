#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "lncdtask",
# ]
#
# [tool.uv.sources]
# lncdtask = { git = "https://github.com/LabNeuroCogDevel/lncdtask" }
# ///

import argparse
import sys
import psychopy
import lncdtask
from lncdtask.lncdtask import LNCDTask, RunDialog, FileLogger, ExternalCom
import pandas as pd

REST_TEXT = "Relax"   #: text displayed during rest/relax block
GRASP_TEXT = "Grasp"  #: text displayed in make a fist block
DEFAULT_NTRIAL = 1    #: number of rest+graps pairs. NTRIAL of each.
DEFAULT_NTR = 4       #: number of counted pulses per individual block
                      #: NB. VESO sequence has pulse for VESO and BOLD. 2 pulses per repetition
TRIGGERS = ["equal"]  #: what key advances the get ready screen? TTL to key via button box


class HandGrasp(LNCDTask):
    """
    Extending lncdtask to display 'grasp' or 'rest'.
    Actual text pulled from onset_df
    """

    def __init__(self, *karg, **kargs):
        super().__init__(*karg, **kargs)

    def block(self, onset, msg):
        """Show grasp/relax text at specified time.
        @param onset time to flip text on
        @param msg   what text to show. ['rest', 'grasp']
        """
        self.msgbox.height = .5
        self.msgbox.text = msg
        textcolor=[1,1,1]
        if msg == GRASP_TEXT:
            textcolor=[1,-.3,-.3] # red
        self.msgbox.setColor(textcolor,'rgb') # white
        self.msgbox.draw()
        return self.flip_at(onset, msg)
        
    def instruction(self, msg):
        """Show message and wait for any keyboard resonse.
        Return keyboard response for processsing with run_instructions
        @param msg instructions for this slide"""
        self.win.flip()
        resp = self.msg(msg)
        return resp

    def finished(self, msg):
        "Finish message in a new color."
        prev_bgcolor = self.win.color
        self.msgbox.height = .1
        self.msgbox.setColor([-1,-1,-1],'rgb')
        self.win.setColor([.3,.3,.3],'rgb')

        self.win.flip()
        self.win.color = prev_bgcolor
        # ^ likely last flip don't need to change back. safer
        # v likewise, return value likely doesn't matter
        return self.msg(msg)

    def get_ready(self, triggers=TRIGGERS):
        """Wait for scanner trigger.
        TODO: add to lncdtask. see screen.wait_for_scanner()"""
        print("Waiting for scanner")
        self.msgbox.text = "Waiting for Scanner to start"
        self.msgbox.draw()
        self.win.flip()
        psychopy.event.waitKeys(keyList=triggers)
 

def args_to_settings():
    """
    Command line args to make it a little easier to speed run testing.
    """

    parser = argparse.ArgumentParser(description="Hand Grasp Task")
    parser.add_argument("--subjid", default="XYZ", help="Subject ID")
    parser.add_argument("--ntrials", type=int, default=DEFAULT_NTRIAL, help="Number of trials")
    parser.add_argument("--trs", type=float, default=DEFAULT_NTR, help="Duration of each block in seconds")
    parser.add_argument("--no-instructions", default=False, action="store_true", dest="instructions",
                        help="Skip instructions at the beginning of the task")
    args = parser.parse_args()

    settings = {'subjid': args.subjid,
                'ntrials': args.ntrials,
                'ntr': args.trs,
                'instructions': args.instructions}
    return settings


def main():
    """
    Run the task.
    """

    settings = args_to_settings()

    run_info = RunDialog(
            extra_dict=settings,
            order=['subjid', 'ntrials', 'ntr', 'instructions'])

    if not run_info.dlg_ok():
        return

    # pull in new settings
    # make sure types are as expected after editing (as string)
    settings = run_info.info
    settings['ntrials'] = int(settings['ntrials'])
    settings['ntr'] = int(settings['ntr'])

    # and get a participant object for saving files
    participant = run_info.mk_participant(['grasp'])

    hc = LNCDTask(onset_df=None)
    # escape quits
    hc.gobal_quit_key()

    # record timing to file and to standard out
    logger = FileLogger()
    logger.new(participant.log_path('subj_info'))
    hc.externals.append(logger)
    hc.externals.append(ExternalCom())

    # instructins include specific generated information:
    # how long an and how many trials
    instructions = [
        lambda: hc.instruction("This is the hand grasping task!"),
        lambda: hc.instruction(
            f"When the screen says '{CLASP_TEXT}',\n"
            + "continually make a fist and release.\n\n"
            #+ f"Repeat for {settings.get('ntr')} TRs\n\n\n"
            + "It is important to continue to keep your head still,\n"
            + "even when making a fist.\n"
            + "We want to get good picture of your brain!"
        ),
        lambda: hc.instruction(
            f"When the screen says '{REST_TEXT}',\n"
            + "rest your hand and stay still."
        ),
        lambda: hc.instruction(f"We'll do this {onset_df.shape[0]//2} times."),
        lambda: hc.instruction("graps = make many fists\n"
                               + "relax = rest\n\n"
                               + "Ready?!"),
    ]

    # if no instructions request, just show the last one
    if settings['instructions']:
        hc.run_instructions(instructions)

    # ### START TASK ###

    # wait for scanner trigger
    hc.get_ready()

    for i in range(settings['ntrials']):
        for block in (REST_TEXT, GRASP_TEXT):
            hc.block(0, block)
            block_ntr = 0
            while block_ntr < settings['ntr']:
                tr_on = psychopy.event.waitKeys(keyList=TRIGGER)
                block_ntr = block_ntr + 1

    hc.finished("Done!\nThank you!")

    # save complete event info.
    #hc.onset_df.to_csv(participant.run_path('subj_info'))


if __name__ == "__main__":
    main()
