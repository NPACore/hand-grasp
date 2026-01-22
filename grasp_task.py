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

import psychopy
from lncdtask import lncdtask
import pandas as pd

TRIGGERS = ["equal"]  #: what key advances the get ready screen?


class HandClasp(lncdtask.LNCDTask):
    """
    Extending lncdtask to display 'clasp' or 'rest'.
    Actual text pulled from onset_df
    """

    def __init__(self, *karg, **kargs):
        super().__init__(*karg, **kargs)
        self.add_event_type("clasp", self.block, ["onset", "text"])
        self.add_event_type("rest", self.block, ["onset", "text"])

    def block(self, onset, msg):
        """Show grasp/relax text at specified time.
        @param onset time to flip text on
        @param msg   what text to show
        """
        # self.trialnum = self.trialnum + 1
        self.msgbox.text = msg
        self.msgbox.draw()
        return self.flip_at(onset)

    def instruction(self, msg):
        """Show message and wait for any keyboard resonse.
        Return keyboard response for processsing with run_instructions
        @param msg instructions for this slide"""
        self.win.flip()
        resp = self.msg(msg)
        return resp

    def get_ready(self, triggers=["equals"]):
        """Wait for scanner trigger. TODO: add to lncdtask"""
        print("Waiting for scanner")
        self.msgbox.text = "Waiting for Scanner to start"
        self.msgbox.draw()
        self.win.flip()
        psychopy.event.waitKeys(keyList=triggers)

    def finished(self, msg):
        "Finish message in a new color."
        prev_bgcolor = self.win.color
        self.win.color = "#666666"
        self.win.flip()
        self.win.color = prev_bgcolor
        # ^ likely last flip don't need to change back. safer
        # v likewise, return value likely doesn't matter
        return self.msg(msg)


def gen_timing(n, dur, clasp_text="Clasp", rest_text="Relax"):
    """
    Generate event timing dataframe. Columns: 'onset', 'text','event'
    >>> d = gen_timing(10, 5)
    >>> d.shape == (10*2,3) # 3 columns. twice as many events as trials
    # first onset is zero, so off-by-one in total duration
    >>> d.at[0,'onset'] = 0
    >>> d.at[d.shape[0]-1,'onset'] = (10-1)*2*5
    """
    text = {"clasp": clasp_text, "rest": rest_text}
    events = text.keys()
    event_list = [
        {"event_name": e, "text": text[e], "onset": dur * (2 * i + ei)}
        for i in range(n)
        for ei, e in enumerate(events)
    ]
    return pd.DataFrame(event_list)


def main():
    """
    Run the task.
    """
    block_dur = 5
    onset_df = gen_timing(2, block_dur)
    hc = HandClasp(onset_df=onset_df)

    instructions = [
        lambda: hc.instruction("This is the hand grasping task!"),
        lambda: hc.instruction(
            "When the screen says 'grasp',\n"
            + "make a fist and release.\n"
            + f"Repeat for {block_dur} seconds\n\n\n"
            + "It is important to continue to keep your head still,\n"
            + "even when making a fist.\n"
            + "We want to get good picture of your brain!"
        ),
        lambda: hc.instruction(
            "When the screen says 'relax',\n" + "rest your hand and stay still."
        ),
        lambda: hc.instruction(f"We'll do this {onset_df.shape[0]//2} times."),
        lambda: hc.instruction("graps = make fists\n" + "relax = rest\n\nReady?!"),
    ]
    hc.run_instructions(instructions)

    hc.get_ready(triggers=TRIGGERS)
    # need to wait for last block to end
    hc.run(end_wait=block_dur)
    hc.finished("Done!\nThank you!")


if __name__ == "__main__":
    main()
