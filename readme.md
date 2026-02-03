# Hand Grasp Task
Quick psychopy implementaiton using the [lncdtask](//github.com/LabNeuroCogDevel/lncdtask) wrapper.

```
uv run --script grasp_task.py --no-instructions --dur .5 --ntrials 1 --subjid AAA
```

## MacOS psychoPy
> [!WARNING]
> This is a dead end? Will need to rewrite lncdtask to avoid Qt for it to work
> Error message from
> 2026-01-23: "Sorry, "PsychoPy" cannot be run on this version of macOS. Qt requires macOS 13.0.0 or later, you have macOS 12.7.5."

```
export \
 PATH="/Applications/PsychoPy.app/Contents/MacOS:/Applications/PsychoPy.app/Contents/Resources:$PATH" \
 PYTHONUSERBASE="$HOME/.psychopy3/packages" \
 PYTHONHOME=/Applications/PsychoPy.app/Contents/Resources \
 PYTHONPATH="$HOME/.psychopy3/packages:$HOME/.psychopy3/packages/lib/python/site-packages:/Applications/PsychoPy.app/Contents/Resources" \
 GIT_PYTHON_GIT_EXECUTABLE=/Applications/PsychoPy.app/Contents/Resources/git-core/git \

python -m pip install --target $HOME/.psychopy3/packages --verbose git+https://github.com/LabNeuroCogDevel/lncdtask
./grasp_task.py --no-instructions --dur .5 --ntrials 1 --subjid AAA
```

