-------------------------------------
Intel(R) MPI Benchmarks for Linux* OS
README
-------------------------------------

------------
Introduction
------------
The Intel(R) MPI Benchmarks provides a set of elementary MPI1 benchmarks.
You can run all of the supported benchmarks, or a subset specified in the
command line using one executable file. The rules, such as time measurement,
message lengths, and selection of communicators are command-line parameters.


----------
What's New
----------
The Intel(R) MPI Benchmarks 3.2.3 is an update release of the 
Intel(R) MPI Benchmarks 3.2 Update 2.

This release includes the following updates compared to the Intel(R) MPI
Benchmarks 3.2 Update 2 (see product documentation for more details):


- New command-line option -msglog to control the maximum allocated 
  message length
- New option -thread_level to specify the desired thread level support
  for MPI_Init_thread.
- Thread safety support in the MPI initialization phase

--------------------
News in 3.2 Update 2
--------------------

The Intel(R) MPI Benchmarks 3.2 Update 2 is an update release of the
Intel(R) MPI Benchmarks 3.2 Update 1.

- Support for large buffers greater than 2 GB for some MPI benchmarks
- New benchmarks PingPongSpecificSource and PingPingSpecificSource. The exact
  destination rank is used for these tests instead of MPI_ANY_SOURCE as in 
  PingPong and PingPing tests.
  Use the include option to enable new benchmarks. For instance, include 
  PingPongSpecificSource PingPingSpecificSource
- New options -include/-exclude to better control benchmarks list
    
-----------
News in 3.2
-----------

Compared to its predecessors, IMB 3.2 has one other default setting:

-Run time control

   IMB dynamically computes a repetition count for each experiment so that
   the sum of the resulting repetitions (roughly) does not exceed a given
   run time. The run time for each sample (= 1 message size with repetitions)
   is set in => IMB_settings.h, IMB_settings_io.h (current value: 10 seconds,
   preprocessor variable SECS_PER_SAMPLE)

   To override this behavior, use the flag -time



Calling sequence (the command line will be repeated in Output table):


IMB-MPI1    [-h{elp}]
            [-npmin     <NPmin>]
            [-multi     <MultiMode>]
            [-off_cache <cache_size[,cache_line_size]>
            [-iter      <msgspersample[,overall_vol[,msgs_nonaggr]]>
            [-time      <max_runtime per sample>]
            [-mem       <max. per process memory for overall message buffers>]
            [-msglen    <Lengths_file>]
            [-map       <PxQ>]
            [-input     <filename>]
            [-include   [benchmark1 [,benchmark2 [,...]]]]
            [-exclude   [benchmark1 [,benchmark2 [,...]]]]
            [benchmark1 [,benchmark2 [,...]]]
            [-msglog    [<minlog>:]<maxlog>]

where

- h ( or help) just provides basic help
  (if active, all other arguments are ignored)

- npmin

  the argument after npmin is NPmin,
  the minimum number of processes to run on
  (then if IMB is started on NP processes, the process numbers
   NPmin, 2*NPmin, ... ,2^k * NPmin < NP, NP are used)
   >>>
   to run on just NP processes, run IMB on NP and select -npmin NP
   <<<
  default:
  NPmin=2

- off_cache

  the argument after off_cache can be either 1 single number (cache_size),
  or 2 comma separated numbers (cache_size,cache_line_size), or just -1

  By default, without this flag, the communications buffer is
  the same within all repetitions of one message size sample;
  most likely, cache re-usage is yielded and thus throughput results
  that might be non realistic.

  With -off_cache, it is attempted to avoid cache re-usage.
  cache_size is a float for an upper bound of the size of the last level cache
  in MBytes cache_line_size is assumed to be the size (Bytes) of a last level
  cache line (can be an upper estimate). The sent/recv'd data are stored in
  buffers of size ~ 2 x MAX( cache_size, message_size ); when repetitively
  using messages of a particular size, their addresses are advanced within those
  buffers so that a single message is at least 2 cache lines after the end of
  the previous message. Only when those buffers have been marched through
  (eventually), they will re-used from the beginning.

  A cache_size and a cache_line_size are assumed as statically defined
  in  => IMB_mem_info.h; these are used when -off_cache -1 is entered

  remark: -off_cache is effective for IMB-MPI1, IMB-EXT, but not IMB-IO

  examples
   -off_cache -1 (use defaults of IMB_mem_info.h);
   -off_cache 2.5 (2.5 MB last level cache, default line size);
   -off_cache 16,128 (16 MB last level cache, line size 128);

  NOTE: the off_cache mode might also be influenced by eventual internal
        caching with the MPI library. This could make the interpretation
        intricate.

  default:
  no cache control, data likely to come out of cache most of the time

- iter

  the argument after -iter can be 1 single, 2 comma separated, or 3 comma
  separated integer numbers, which override the defaults MSGSPERSAMPLE,
  OVERALL_VOL, MSGS_NONAGGR of =>IMB_settings.h examples
   -iter 2000        (override MSGSPERSAMPLE by value 2000)
   -iter 1000,100    (override OVERALL_VOL by 100)
   -iter 1000,40,150 (override MSGS_NONAGGR by 150)

  default:
  iteration control through parameters MSGSPERSAMPLE,OVERALL_VOL,MSGS_NONAGGR =>
  IMB_settings.h

  NOTE: New in versions from IMB 3.2 on
        the iter selection is overridden by a dynamic selection that is a new
        default in IMB 3.2: when a maximum run time (per sample) is expected to
        be exceeded, the iteration number will be cut down; see -time flag

- time

  the argument after -time is a float, specifying that
  a benchmark will run at most that many seconds per message size
  the combination with the -iter flag or its defaults is so that always
  the maximum number of repetitions is chosen that fulfills all restrictions
  example
   -time 0.150       (a benchmark will run at most 150 milli seconds
                      per message size, if the default (or -iter selected)
                      number of repetitions would take longer than that)

  remark: per sample, the rough number of repetitions to fulfill the -time
          request is estimated in preparatory runs that use ~ 1 second overhead

  default:
  A fixed time limit SECS_PER_SAMPLE =>IMB_settings.h; currently set to 10
  (new default in IMB_3.2)

- mem

  the argument after -mem is a float, specifying that
  at most that many GB are allocated per process for the message buffers
  if the size is exceeded, a warning will be output, stating how much memory
  would have been necessary, but the overall run is not interrupted
  example
   -mem 0.2          (restrict memory for message buffers to 200 MB per
                      process)

  default:
  the memory is restricted by MAX_MEM_USAGE => IMB_mem_info.h

- map

  the argument after -map is PxQ, P,Q are integer numbers with P*Q <= NP
  enter PxQ with the 2 numbers separated by letter "x" and no blancs
  the basic communicator is set up as P by Q process grid

  if, for example, you run on N nodes of X processors each, and inserts
  P=X, Q=N, then the numbering of processes is "inter node first"
  running PingPong with P=X, Q=2 would measure inter-node performance
  (assuming MPI default would apply 'normal' mapping, that is fill nodes
  first priority)

  default:
  Q=1

- multi

  the argument after -multi is MultiMode (0 or 1)

  if -multi is selected, running the N process version of a benchmark
  on NP overall, means running on (NP/N) simultaneous groups of N each.

  MultiMode only controls default (0) or extensive (1) output charts.
  0: only lowest performance groups is output
  1: all groups are output

  default:
  multi off

- msglen

  the argument after -msglen is a lengths_file, an ASCII file, containing any
  set of nonnegative message lengths, one per line

  default:
  no lengths_file, lengths defined by settings.h, settings_io.h

- input

  the argument after -input is a filename that contains, line by
  line, benchmark names facilitates running particular benchmarks as compared to
  using the command line.

  default:
  no input file exists
  
- include
  the argument after -include  is one or more benchmark names separated by 
  spaces
  
  default:
  no additional benchmarks to include
      
- exclude
  the argument after -exclude is one or more benchmark names separated by 
  spaces
        
  default:
  no any benchmarks to exclude
                                          
- benchmarkX is (in arbitrary lower/upper case spelling)

PingPong
PingPing
Sendrecv
Exchange
Bcast
Allgather
Allgatherv
Gather
Gatherv
Scatter
Scatterv
Alltoall
Alltoallv
Reduce
Reduce_scatter
Allreduce
Barrier

-msglog 

   the option allows you to control the lengths of transfer messages. If
   it is specified the sizes 0, 2^i ( i=minlog...maxlog), the setting
   overrides the MINMSGLOG and MAXMSGLOG hard-coded values.

   default:
   MINMSGLOG:MAXMSGLOG

--------------------------------
Disclaimer and Legal Information
--------------------------------

INFORMATION IN THIS DOCUMENT IS PROVIDED IN CONNECTION WITH INTEL PRODUCTS. 
NO LICENSE, EXPRESS OR IMPLIED, BY ESTOPPEL OR OTHERWISE, TO ANY INTELLECTUAL 
PROPERTY RIGHTS IS GRANTED BY THIS DOCUMENT. EXCEPT AS PROVIDED IN INTEL'S TERMS 
AND CONDITIONS OF SALE FOR SUCH PRODUCTS, INTEL ASSUMES NO LIABILITY WHATSOEVER, 
AND INTEL DISCLAIMS ANY EXPRESS OR IMPLIED WARRANTY, RELATING TO SALE AND/OR USE 
OF INTEL PRODUCTS INCLUDING LIABILITY OR WARRANTIES RELATING TO FITNESS FOR A 
PARTICULAR PURPOSE, MERCHANTABILITY, OR INFRINGEMENT OF ANY PATENT, COPYRIGHT OR 
OTHER INTELLECTUAL PROPERTY RIGHT. 
UNLESS OTHERWISE AGREED IN WRITING BY INTEL, THE INTEL PRODUCTS ARE NOT DESIGNED 
NOR INTENDED FOR ANY APPLICATION IN WHICH THE FAILURE OF THE INTEL PRODUCT COULD 
CREATE A SITUATION WHERE PERSONAL INJURY OR DEATH MAY OCCUR.
Intel may make changes to specifications and product descriptions at any time, 
without notice. Designers must not rely on the absence or characteristics of any 
features or instructions marked "reserved" or "undefined." Intel reserves these 
for future definition and shall have no responsibility whatsoever for conflicts 
or incompatibilities arising from future changes to them. The information here 
is subject to change without notice. Do not finalize a design with this 
information. 
The products described in this document may contain design defects or errors 
known as errata which may cause the product to deviate from published 
specifications. Current characterized errata are available on request. 
Contact your local Intel sales office or your distributor to obtain the latest 
specifications and before placing your product order.
Copies of documents which have an order number and are referenced in this 
document, or other Intel literature, may be obtained by calling 1-800-548-4725, 
or go to:  http://www.intel.com/design/literature.htm

Intel processor numbers are not a measure of performance. Processor numbers 
differentiate features within each processor family, not across different 
processor families. Go to: 
http://www.intel.com/products/processor_number/

MPEG-1, MPEG-2, MPEG-4, H.261, H.263, H.264, MP3, DV, VC-1, MJPEG, AC3, AAC, 
G.711, G.722, G.722.1, G.722.2, AMRWB, Extended AMRWB (AMRWB+), G.167, G.168, 
G.169, G.723.1, G.726, G.728, G.729, G.729.1, GSM AMR, GSM FR are international 
standards promoted by ISO, IEC, ITU, ETSI, 3GPP and other organizations. 
Implementations of these standards, or the standard enabled platforms may 
require licenses from various entities, including Intel Corporation.

BlueMoon, BunnyPeople, Celeron, Celeron Inside, Centrino, Centrino Inside, Cilk, 
Core Inside, E-GOLD, i960, Intel, the Intel logo, Intel AppUp, Intel Atom, Intel 
Atom Inside, Intel Core, Intel Inside, Intel Insider, the Intel Inside logo, 
Intel NetBurst, Intel NetMerge, Intel NetStructure, Intel SingleDriver, Intel 
SpeedStep, Intel Sponsors of Tomorrow., the Intel Sponsors of Tomorrow. logo, 
Intel StrataFlash, Intel vPro, Intel XScale, InTru, the InTru logo, the InTru 
Inside logo, InTru soundmark, Itanium, Itanium Inside, MCS, MMX, Moblin, 
Pentium, Pentium Inside, Puma, skoool, the skoool logo, SMARTi, Sound Mark, The 
Creators Project, The Journey Inside, Thunderbolt, Ultrabook, vPro Inside, 
VTune, Xeon, Xeon Inside, X-GOLD, XMM, X-PMU and XPOSYS are trademarks of Intel 
Corporation in the U.S. and other countries. 

* Other names and brands may be claimed as the property of others.

Microsoft, Windows, Visual Studio, Visual C++, and the Windows logo are 
trademarks, or registered trademarks of Microsoft Corporation in the 
United States and/or other countries.

Java is a registered trademark of Oracle and/or its affiliates.

Copyright (C) [2004]-[2011], Intel Corporation. All rights reserved.
