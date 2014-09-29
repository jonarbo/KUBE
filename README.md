KUBE
====

KUBE is a benchmarking and testing framework rather than a benchmarking 'suite', as it is not our objective to gather and define a bunch of applications or software tests along with proper input and output datasets. This latter is the user's responsibility. As a benchmarking and testing framework, our goal is to create a means to drive, centralize, control and organize the benchmarking and testing process in a consistent, flexible and easy to use way. In this
manner any benchmark may be added and managed using KUBE. KUBE also has analysis capabilities built in for viewing and analyzing historical benchmark results.

KUBE is driven by a configuration file that contains rules to be applied in the different stages of the benchmarking/testing process. The configuration file may be specified as an argument, otherwise the default "etc/kube.yaml" file will be used. The user may also develop custom configuration files (for example if you have different machines and environments) and choose to use them as needed.
