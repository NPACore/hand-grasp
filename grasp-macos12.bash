#!/usr/bin/env bash

# from lncdtask.rundialog import RunDialog
#   runs
# from psychopy.gui import DlgFromDict
#   throws error
# > Sorry, "PsychoPy" cannot be run on this version of macOS. Qt requires macOS 13.0.0 or later, you have macOS 12.7.5.

export \
 PATH="/Applications/PsychoPy.app/Contents/MacOS:/Applications/PsychoPy.app/Contents/Resources:$PATH" \
 PYTHONUSERBASE="$HOME/.psychopy3/packages" \
 PYTHONHOME=/Applications/PsychoPy.app/Contents/Resources \
 PYTHONPATH="$HOME/.psychopy3/packages:$HOME/.psychopy3/packages/lib/python/site-packages:/Applications/PsychoPy.app/Contents/Resources" \
 GIT_PYTHON_GIT_EXECUTABLE=/Applications/PsychoPy.app/Contents/Resources/git-core/git \

# python -m pip install --target $HOME/.psychopy3/packages --verbose git+https://github.com/LabNeuroCogDevel/lncdtask
python ./grasp_task.py "$@" # --no-instructions --dur .5 --ntrials 1 --subjid AAA
