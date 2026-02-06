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
from lncdtask.lncdtask import LNCDTask, RunDialog, FileLogger, ExternalCom, create_window
import pandas as pd

REST_TEXT = "Relax"  #: text displayed during rest/relax block
GRASP_TEXT = "Grasp"  #: text displayed in make a fist block
BLOCK_ORDER = (REST_TEXT, GRASP_TEXT)  #: sequence
DEFAULT_NTRIAL = 1  #: number of rest+graps pairs. NTRIAL of each.
DEFAULT_NTR = 4  #: number of counted pulses per individual block
#: NB. VESO sequence has pulse for VESO and BOLD. 2 pulses per repetition
TRIGGERS = [
    "equal"
]  #: what key advances the get ready screen? TTL to key via button box


class HandGrasp(LNCDTask):
    """
    Extending lncdtask to display 'grasp' or 'rest'.
    Actual text pulled from onset_df
    """

    def __init__(self, *karg, **kargs):
        super().__init__(*karg, **kargs)
        # annotation for sequence info
        self.annote = psychopy.visual.TextStim(self.win, text="", name="annotation")
        self.annote.setColor([-0.8, -0.8, -0.8], "rgb")
        self.annote.pos = (0.5, -0.8)  # center-right, bottom of screen

    def block(self, onset, msg):
        """Show grasp/relax text at specified time.
        @param onset time to flip text on
        @param msg   what text to show. ['rest', 'grasp']
        """
        self.msgbox.height = 0.5
        self.msgbox.text = msg
        textcolor = [1, 1, 1]
        if msg == GRASP_TEXT:
            textcolor = [1, -0.3, -0.3]  # red
        self.msgbox.setColor(textcolor, "rgb")  # white
        self.msgbox.draw()
        self.annote.draw()
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
        self.msgbox.height = 0.1
        self.msgbox.setColor([-1, -1, -1], "rgb")
        self.win.setColor([0.3, 0.3, 0.3], "rgb")

        self.win.flip()
        self.win.color = prev_bgcolor
        # ^ likely last flip don't need to change back. but safer
        # v likewise, return value likely doesn't matter
        return self.msg(msg)

    def get_ready(self, triggers=TRIGGERS):
        """Wait for scanner trigger. see lncdtask.screen.wait_for_scanner()"""
        print("Waiting for scanner")
        self.msgbox.text = "Waiting for Scanner to start"
        self.msgbox.draw()
        self.win.flip()
        psychopy.event.waitKeys(keyList=triggers)  # returns key pushed
        starttime = psychopy.core.getTime()
        return starttime

    def add_event(self, onset, event_name, start_time):
        """
        Add minimal event info to onset_df to save.
        Column names mirror those used by fixed-timing within lncdtask.
        onset_df must be initialized with columns: onset, event_name, onset0
        """
        new_row = pd.DataFrame(
            {
                "onset": [onset],
                "event_name": [event_name],
                "onset0": [onset - start_time],
            }
        )
        self.onset_df = pd.concat([self.onset_df, new_row])


def args_to_settings():
    """
    Command line args to make it a little easier to speed run testing.
    """

    parser = argparse.ArgumentParser(description="Hand Grasp Task")
    parser.add_argument("--subjid", default="XYZ", help="Subject ID")
    parser.add_argument(
        "--ntrials", type=int, default=DEFAULT_NTRIAL, help="Number of trials"
    )
    parser.add_argument(
        "--trs",
        type=float,
        default=DEFAULT_NTR,
        help="Duration of each block in seconds",
    )
    parser.add_argument(
        "--instructions",
        default=False,
        action="store_true",
        dest="instructions",
        help="Skip instructions at the beginning of the task",
    )
    parser.add_argument(
        "--annotate",
        default=False,
        action="store_true",
        dest="annotate",
        help="Show TR flips in bottom corner",
    )
    parser.add_argument(
        "--no-fullscreen",
        default=False,
        action="store_true",
        dest="no_fullscreen",
        help="Show TR flips in bottom corner",
    )
    args = parser.parse_args()

    settings = {
        "subjid": args.subjid,
        "ntrials": args.ntrials,
        "ntr": args.trs,
        "annotate": args.annotate,
        "instructions": args.instructions,
        "fullscreen": not args.no_fullscreen
    }
    return settings


def main():
    """
    Run the task.
    """

    settings = args_to_settings()

    run_info = RunDialog(
        extra_dict=settings, order=["subjid", "ntrials", "ntr","annotate", "instructions", "fullscreen"]
    )

    if not run_info.dlg_ok():
        return

    # pull in new settings
    # make sure types are as expected after editing (as string)
    settings = run_info.info
    settings["ntrials"] = int(settings["ntrials"])
    settings["ntr"] = int(settings["ntr"])

    # and get a participant object for saving files
    participant = run_info.mk_participant(["grasp"])

    # onset_df is typically precomputed.
    # kludge: will popoulate as we go so output csv file still has data for GLM
    #         but timing will be determined dynamically/at run time by TR pulses
    empty_df = pd.DataFrame({"onset": [], "event_name": [], "onset0": []})

    win = None # let lncdtask figure it out
    if not settings['fullscreen']:
        win = create_window(False)
    hc = HandGrasp(onset_df=empty_df, win=win)

    # escape quits
    hc.gobal_quit_key()

    # record timing to file and to standard out
    logger = FileLogger()
    logger.new(participant.log_path("grasp"))
    hc.externals.append(logger)  # save events "marked" to a file
    hc.externals.append(ExternalCom())  # and print to terminal

    # instructins include specific generated information:
    # how long an and how many trials
    instructions = [
        lambda: hc.instruction("This is the hand grasping task!"),
        lambda: hc.instruction(
            f"When the screen says '{GRASP_TEXT}',\n"
            + "continually make a fist and release.\n\n"
            # + f"Repeat for {settings.get('ntr')} TRs\n\n\n"
            + "It is important to continue to keep your head still,\n"
            + "even when making a fist.\n"
            + "We want to get good picture of your brain!"
        ),
        lambda: hc.instruction(
            f"When the screen says '{REST_TEXT}',\n" + "rest your hand and stay still."
        ),
        lambda: hc.instruction(f"We'll do this {settings.get('ntrials')} times."),
        lambda: hc.instruction(
            f"{GRASP_TEXT} = make many fists\n" + f"{REST_TEXT} = rest\n\n" + "Ready?!"
        ),
    ]

    # if no instructions request, just show the last one
    if settings["instructions"]:
        hc.run_instructions(instructions)

    # track two TR times. likely BOLD volume and then VASO volume
    tr_times = [0, 0]
    # wait for scanner trigger.
    # This is pulse is recieved precieding the first volume that's collected
    start_pulse_time = hc.get_ready()
    hc.mark_external(f"STARTING: recieved first TR pulse {start_pulse_time}")

    # ### START TASK ###
    for block_i in range(settings["ntrials"]):
        for block_text in BLOCK_ORDER:
            # drawing will flip after TR pulse recieved. A delay of 10ish milliseconds?
            # will send externals (print and mark in file)
            # see block onset compared to "STARTING" onset
            if settings.get("annotate"):
                hc.annote.text = (
                    f"{block_i} x {block_text} {tr_times[0]:0.3f} {tr_times[1]:0.3f}"
                )
            block_on_time = hc.block(0, block_text)

            # have drawn and flipped. have some time to do computaiton before need to recieve key
            hc.add_event(
                onset=block_on_time.get("flip", 0),
                event_name=block_text,
                start_time=start_pulse_time,
            )

            # count number of TRs. used on first pass to get TR of BOLD and VASO
            # for logging only. Doesn't change task presentation
            # on the very first block, the first tr capture was eaten by the get ready screen.
            if block_i == 0 and block_text == BLOCK_ORDER[0]:
                block_ntr = 1
                tr_prev = start_pulse_time
            else:
                block_ntr = 0
                # tr_prev set by previous block

            # wait until we've seen enough TRs. log each one.
            while block_ntr < settings["ntr"]:
                psychopy.event.waitKeys(keyList=TRIGGERS)
                tr_on = psychopy.core.getTime()
                hc.mark_external(
                    f"Pulse {block_ntr} for block {block_i} recieved {tr_on}"
                )

                # capture TR difference for logging and file name
                mod_i = block_ntr % 2
                if tr_times[mod_i] == 0:
                    tr_times[mod_i] = tr_on - tr_prev
                    hc.mark_external(f"TR {mod_i} is {tr_times[mod_i]}")
                tr_prev = tr_on

                # only need once more, to capture second seen (but first in pair) TR
                block_ntr = block_ntr + 1

                # represent ever TR?
                if settings.get("annotate"):
                    hc.annote.text = f"{block_i} {block_ntr} {block_text} {tr_times[0]:0.3f} {tr_times[1]:0.3f}"
                    hc.annote.draw()
                    hc.msgbox.draw()
                    hc.win.flip()

    hc.finished("Done!\nThank you!")

    # save complete event info.
    hc.onset_df.to_csv(
        participant.run_path(f"grasp_tr1-{tr_times[0]:0.3f}_tr2-{tr_times[1]:0.3f}")
    )


if __name__ == "__main__":
    main()
