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
CLASP_TEXT = "Grasp"  #: text displayed in make a fist block
DEFAULT_NTRIAL = 10
DEFAULT_DUR = 20
TRIGGERS = ["equal"]  #: what key advances the get ready screen?


# monkey patch
def wait_until_monkey(stoptime):
    """copy of lncdtask.screen.wait_util but with key handing"""
    while psychopy.core.getTime() < stoptime:
        print("WAIT")
        psychopy.event.getKeys(clear=False)
        psychopy.core.wait(1.001)

# TODO: doesn't work
lncdtask.lncdtask.wait_util = wait_until_monkey


class HandGrasp(LNCDTask):
    """
    Extending lncdtask to display 'grasp' or 'rest'.
    Actual text pulled from onset_df
    """

    def __init__(self, *karg, **kargs):
        super().__init__(*karg, **kargs)
        self.add_event_type("grasp", self.block, ["onset", "text"])
        self.add_event_type("rest", self.block, ["onset", "text"])

    def block(self, onset, msg):
        """Show grasp/relax text at specified time.
        @param onset time to flip text on
        @param msg   what text to show
        """
        # self.trialnum = self.trialnum + 1
        self.msgbox.text = msg
        self.msgbox.draw()
        # NB. msg here gets forward onto marks (file log)
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
        self.win.color = "#666666"
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
 



def gen_timing(n, dur):
    """
    Generate event timing dataframe. Columns: 'onset', 'text','event_name'
    onset goes from 0 to the start time of last block
    Each row is a block. event_name is 'grasp' or 'rest'
    'text' is what to show on screen: either `REST_TEXT` or `CLASP_TEXT`.
    >>> d = gen_timing(10, 5)
    >>> d.shape == (10*2,3) # 3 columns. twice as many events as trials
    # first onset is zero, so off-by-one in total duration
    >>> d.at[0,'onset'] = 0
    >>> d.at[d.shape[0]-1,'onset'] = (10-1)*2*5
    """
    text = {"grasp": CLASP_TEXT, "rest": REST_TEXT}
    events = text.keys()
    event_list = [
        {"event_name": e,
         "text": text[e],
         "onset": dur * (2 * i + ei)}
        for i in range(n)
        for ei, e in enumerate(events)
    ]
    return pd.DataFrame(event_list)


def args_to_settings():
    """
    Command line args to make it a little easier to speed run testing.
    """

    parser = argparse.ArgumentParser(description="Hand Grasp Task")
    parser.add_argument("--subjid", default="XYZ", help="Subject ID")
    parser.add_argument("--ntrials", type=int, default=DEFAULT_NTRIAL, help="Number of trials")
    parser.add_argument("--dur", type=float, default=DEFAULT_DUR, help="Duration of each block in seconds")
    parser.add_argument("--no-instructions", action="store_false", dest="instructions",
                        help="Skip instructions at the beginning of the task")
    args = parser.parse_args()

    settings = {'subjid': args.subjid,
                'ntrials': args.ntrials,
                'dur': args.dur,
                'instructions': args.instructions}
    return settings


def main():
    """
    Run the task.
    """

    settings = args_to_settings()

    run_info = RunDialog(
            extra_dict=settings,
            order=['subjid', 'ntrials', 'dur', 'instructions'])

    if not run_info.dlg_ok():
        return

    # pull in new settings
    # make sure types are as expected after editing (as string)
    settings = run_info.info
    settings['ntrials'] = int(settings['ntrials'])
    settings['dur'] = float(settings['dur'])

    # use settings to pre-construct full timing schedule of task events
    onset_df = gen_timing(settings['ntrials'], settings['dur'])

    # and get a participant object for saving files
    participant = run_info.mk_participant(['grasp'])

    hc = HandGrasp(onset_df=onset_df, participant=participant)
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
            + "continually make a fist and release.\n"
            + f"Repeat for {settings.get('dur')} seconds\n\n\n"
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
    if not settings['instructions']:
        instructions = instructions[-1:]

    # ### START TASK ###

    hc.run_instructions(instructions)
    # wait for scanner trigger
    hc.get_ready()
    # need to wait for last block to end
    hc.run(end_wait=settings['dur'])
    hc.finished("Done!\nThank you!")

    # save complete event info.
    # includes run order expected and exact flip times
    hc.onset_df.to_csv(participant.run_path('subj_info'))


if __name__ == "__main__":
    main()
