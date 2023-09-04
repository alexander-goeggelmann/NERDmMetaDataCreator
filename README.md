# NERDm MetaData Creator
User interface to create MetaData in json format based on NIST NERDm

A tool/editor to generate meta data following the NERDm json schma of NIST https://data.nist.gov/od/dm/nerdm/.
It is based on python.
Also make sure to install the following packages:

- json
- tkinter
- panel
Following system packages are needed (in general they do not need to be installed):

- os
- requests (VERY IMPORTANT: Make sure to write the name correctly! Other packages with similar names, like 'request' are malware!)
- datetime
  
In order to execute the program, the .py file, follow the following steps:
If necessary, the proxy value has to be set in the .py file.

The file can be executed with
> python MetaDataCreatorNoProxy.py
  
One can also execute the .py in jupyter, without including any packages (but have to be installed), with the following command:
> %run MetaDataCreator.py
  
Eventually, if the .py file is not in the same directory as the working directory, one has to add the absolute or relative path, e.g.:
> %run ".\path_to_file\MetaDataCreatorNoProxy.py"

