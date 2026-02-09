# Hand Grasp Task
Quick [psychopy](https://www.psychopy.org/) implementaiton using the [lncdtask](//github.com/LabNeuroCogDevel/lncdtask) wrapper.

  * `./grasp_trcount.py` - specify number of TRs per block
  * `./grasp_task.py` - specify duration of blocks

```
uv run --script ./grasp_trcount.py --no-dialog --no-logging --no-fullscreen --ntr 3 --ntrial 1 --annotate
```

## Outputs

```
subj_info/
└── sub-AAA
    └── ses-01
        └── 20260205_grasp
            ├── grasp_tr1-0.576_tr2-0.448-1770315169.csv
            └── log
                └── grasp-1770315164.log
```

Completed runs have a csv file like `subj_info/sub-*/ses-*/{YYYYMMDD}_grasp/grasp_tr1-*_tr2-*-{epochtime}.csv` useful for GLM timing input. 
File name also includes 2 observed TRs (likely BOLD and VASO).


```
cat subj_info/sub-AAA/ses-01//20260205_grasp/grasp_tr1-0.576_tr2-0.448-1770315169.csv

,onset,event_name,onset0
0,5.190117120742798,Relax,0.034680843353271484
0,6.690381765365601,Grasp,1.5349454879760742
```

All runs save a log like `subj_info/sub-*/ses-*/{yyymmdd}_grasp/log/grasp-{epochtime}.log`. 
Format is lines containing "marks": `epoch seconds` at observation  and `description` of the observations
```
cat subj_info/sub-AAA/ses-01//20260205_grasp/log/grasp-1770315164.log

1770315164.44887 STARTING: recieved first TR pulse 5.155436277389526
1770315164.48355 Relax
1770315164.89645 Pulse 1 for block 0 recieved 5.603025197982788
1770315164.89650 TR 1 is 0.4475889205932617
1770315165.47247 Pulse 2 for block 0 recieved 6.179050922393799
1770315165.47251 TR 0 is 0.5760257244110107
1770315165.95255 Pulse 3 for block 0 recieved 6.659131288528442
1770315165.98382 Grasp
1770315166.43254 Pulse 0 for block 0 recieved 7.139124631881714
1770315166.92853 Pulse 1 for block 0 recieved 7.635113000869751
1770315167.42454 Pulse 2 for block 0 recieved 8.131099939346313
1770315167.93649 Pulse 3 for block 0 recieved 8.64306116104126
```

> [!NOTE]
> This example task log is from interactive testing: pushing "=" instead of recieving it from the scanner.
> However, START to first relax is TR independent. Ideally would be 0 seconds but here is **346.8 ms** (`1770315164.48355 - 1770315164.44887`)!
> This is the time from when the scanner starts collecting the first volume to when the screen actually shows the task start

## Usage

To run offline (on windows), install [psychopy](https://www.psychopy.org/download.html) and copy the [lncdtask](//github.com/LabNeuroCogDevel/lncdtask) repo as directory within this project.

## Development

Run with [`uv`](https://docs.astral.sh/uv/) to avoid manual venv managment.
```
uv run --script ./grasp_trcount.py --instructions --ntr 4 --ntrials 1 --subjid AAA
```
