---------------------------------------
Intel(R) MPI Benchmarks for Windows* OS
README
---------------------------------------

------------
Introduction
------------
The Intel® MPI Benchmarks provides a set of elementary benchmarks.
You can run all of the supported benchmarks, or a subset specified in the
command line using one executable. The rules, such as time measurement,
message lengths, and selection of communicators are command-line parameters.

-------------------
Product Directories
-------------------
The Windows OS* part of Intel(R) MPI Benchmarks 3.2.2 has the following
subdirectories:

  - .\IMB-EXT_VS_2005 (Microsoft* Visual Studio* 2005 project folder)
  - .\IMB-EXT_VS_2008 (Microsoft* Visual Studio* 2008 project folder)
  - .\IMB-IO_VS_2005  (Microsoft* Visual Studio* 2005 project folder)
  - .\IMB-IO_VS_2008  (Microsoft* Visual Studio* 2008 project folder)
  - .\IMB-MPI1_VS_2005 (Microsoft* Visual Studio* 2005 project folder)
  - .\IMB-MPI1_VS_2008 (Microsoft* Visual Studio* 2008 project folder)

Note that the Microsoft* Visual Studio* project folders IMB-EXT_VS_2005,
IMB-EXT_VS_2008, IMB-IO_VS_2005, IMB-IO_VS_2008, IMB-MPI1_VS_2005, and
IMB-MPI1_VS_2008 are applicable only to Microsoft* Windows* OS. Some
familiarity with Microsoft* Visual Studio* and the Windows Cluster* at
hand is assumed. This README document does not provide complete guidance.

The solutions are based on an install of Intel(R) MPI Library for Windows
(see the environment variable I_MPI_ROOT).

The internal folder structure for these Microsoft* Visual Studio* projects
look the following:
                 ...
    |
    +--\IMB-EXT_VS_2005
    |   |
    |   +--\Debug
    |   |
    |   +--\Release
    |   |
    |   +--\x64
    |   |   |
    |   |   +--\Debug
    |   |   |
    |   |   +--\Release
    |   |
    |   +--IMB-EXT.rc
    |   |
    |   +--IMB-EXT.sln
    |   |
    |   +--IMB-EXT.vcproj
    |   |
    |   +--resource.h
    |
    +--\IMB-EXT_VS_2008
    |   |
    |   +--\Debug
    |   |
    |   +--\Release
    |   |
    |   +--\x64
    |   |   |
    |   |   +--\Debug
    |   |   |
    |   |   +--\Release
    |   |
    |   +--IMB-EXT.rc
    |   |
    |   +--IMB-EXT.sln
    |   |
    |   +--IMB-EXT.vcproj
    |   |
    |   +--resource.h
    |
    +--\IMB-IO_VS_2005
    |   |
    |   +--\Debug
    |   |
    |   +--\Release
    |   |
    |   +--\x64
    |   |   |
    |   |   +--\Debug
    |   |   |
    |   |   +--\Release
    |   |
    |   +--IMB-IO.rc
    |   |
    |   +--IMB-IO.sln
    |   |
    |   +--IMB-IO.vcproj
    |   |
    |   +--resource.h
    |
    +--\IMB-IO_VS_2008
    |   |
    |   +--\Debug
    |   |
    |   +--\Release
    |   |
    |   +--\x64
    |   |   |
    |   |   +--\Debug
    |   |   |
    |   |   +--\Release
    |   |
    |   +--IMB-IO.rc
    |   |
    |   +--IMB-IO.sln
    |   |
    |   +--IMB-IO.vcproj
    |   |
    |   +--resource.h
    |
    +--\IMB-MPI1_VS_2005
    |   |
    |   +--\Debug
    |   |
    |   +--\Release
    |   |
    |   +--\x64
    |   |   |
    |   |   +--\Debug
    |   |   |
    |   |   +--\Release
    |   |
    |   +--IMB-MPI1.rc
    |   |
    |   +--IMB-MPI1.sln
    |   |
    |   +--IMB-MPI1.vcproj
    |   |
    |   +--resource.h
    |
    +--\IMB-MPI1_VS_2008
        |
        +--\Debug
        |
        +--\Release
        |
        +--\x64
        |   |
        |   +--\Debug
        |   |
        |   +--\Release
        |
        +--IMB-MPI1.rc
        |
        +--IMB-MPI1.sln
        |
        +--IMB-MPI1.vcproj
        |
        +--resource.h
 
The "Debug" and "Release" subfolders above that are at the same level as the
"x64" subfolder are for "Win32" solutions.

When the Intel(R) MPI Benchmarks 3.2.1 is installed on a Microsoft* Windows*
operating system, click on the respective ".vcproj" project file and
use the Microsoft* Visual Studio* menu to run the associated benchmark
application.

Within the Microsoft Windows Explorer*, go to one of the folders IMB-EXT_VS_2005, 
IMB-EXT_VS_2008, IMB-IO_VS_2005, IMB-IO_VS_2008, IMB-MPI1_VS_2005, or 
IMB-MPI1_VS_2008 and click on the corresponding ".vcproj" file.

To Build "x64" Executable files for the Intel(R) MPI Benchmarks
----------------------------------------------------------

From the Visual Studio Project panel:
1) Change the "Solution Platforms" dialog box to "x64".
2) Change the "Solution Configurations" dialog box to "Release".
3) Check other settings in the usual style, for example
      General->Project Defaults 
         Change "Character Set" to "Use Multi-Byte Character Set"
      C/C++->General 
         "Additional Include Directories", here set to "$(I_MPI_ROOT)\em64t\include".
         "Warning Level", set the warning level to "Level 1 (/W1)"
      C/C++->Preprocessor
         For the row "Preprocessor definitions" within the Visual Studio projects
         IMB-EXT_VS_2005, and IMB-EXT_VS_2008, add the conditional compilation macros
         WIN_IMB, _CRT_SECURE_NO_DEPRACATE, and EXT
         For the row "Preprocessor definitions" within the Visual Studio projects
         IMB-IO_VS_2005, and IMB-IO_VS_2008, add the conditional compilation macros
         WIN_IMB, _CRT_SECURE_NO_DEPRACATE, and MPIIO
         For the row "Preprocessor definitions" within the Visual Studio projects
         IMB-MPI1_VS_2005, and IMB-MPI1_VS_2008, add the conditional compilation macros
         WIN_IMB, _CRT_SECURE_NO_DEPRACATE, and MPI1
      Linker->Input
         "Additional Dependencies", here "$(I_MPI_ROOT)\em64t\lib\impi.lib". Be sure to
         add quotes.

4) Use F7 or Build->Build Solution to create an executable

To Build "Win32" Executables for the Intel(R) MPI Benchmarks
------------------------------------------------------------

From the Microsoft Windows Control Panel, adjust the system environment variables for
Include, Lib, and Path so that if they respectively have the following settings:

  C:\Program Files (x86)\Intel\ICTCE\4.0.0.020\mpi\em64t\include
  C:\Program Files (x86)\Intel\ICTCE\4.0.0.020\mpi\em64t\lib
  C:\Program Files (x86)\Intel\ICTCE\4.0.0.020\mpi\em64t\bin

at the beginning of the Variable Value dialog panel, then these panels should be changed
from subfolders referencing "em64t" to "ia32":

  C:\Program Files (x86)\Intel\ICTCE\4.0.0.020\mpi\ia32\include
  C:\Program Files (x86)\Intel\ICTCE\4.0.0.020\mpi\ia32\lib
  C:\Program Files (x86)\Intel\ICTCE\4.0.0.020\mpi\ia32\bin

After checking out the settings of these environment variables and saving any necessary
changes via the Microsoft Windows Control Panel*, one can proceed to open the relevant
Visual Studio 2005* or Visual Studio 2008* projects under the WINDOWS subfolder for the
Intel(R) MPI Benchmarks.

From the Visual Studio Project panel:
1) Change the "Solution Platforms" dialog box to "Win32".
2) Change the "Solution Configurations" dialog box to "Release".
3) Check other settings in the usual style, for example
      General->Project Defaults 
         Change "Character Set" to "Use Multi-Byte Character Set"
      C/C++->General 
         "Additional Include Directories", here set to "$(I_MPI_ROOT)\ia32\include".
         "Warning Level", set the warning level to "Level 1 (/W1)"
      C/C++->Preprocessor
         For the row "Preprocessor definitions" within the Visual Studio projects
         IMB-EXT_VS_2005, and IMB-EXT_VS_2008, add the conditional compilation macros
         WIN_IMB, _CRT_SECURE_NO_DEPRACATE, and EXT
         For the row "Preprocessor definitions" within the Visual Studio projects
         IMB-IO_VS_2005, and IMB-IO_VS_2008, add the conditional compilation macros
         WIN_IMB, _CRT_SECURE_NO_DEPRACATE, and MPIIO
         For the row "Preprocessor definitions" within the Visual Studio projects
         IMB-MPI1_VS_2005, and IMB-MPI1_VS_2008, add the conditional compilation macros
         WIN_IMB, _CRT_SECURE_NO_DEPRACATE, and MPI1
      Linker->Input
         "Additional Dependencies", here "$(I_MPI_ROOT)\ia32\lib\impi.lib". Be sure to
         add quotes.

4) Use F7 or Build->Build Solution to create an executable

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

Copyright (C) [2007]-[2011], Intel Corporation. All rights reserved.


