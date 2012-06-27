#! /bin/bash
#
# @ output = Hg_%j.out
# @ error =  Hg_%j.err
# @ total_tasks =8
# @ cpus_per_task =  2
# @ wall_clock_limit = 20:00
# @ class = benchmark 
# @ mining_level = 0

export EXE=/gpfs/apps/VASP/src/5.2.11/IBM/VASP_5.2.11/vasp.5.2/vasp.x.complex
export EXE=/gpfs/apps/VASP/5.2.11_jan2011/vasp.x.complex
time srun ${EXE} 



