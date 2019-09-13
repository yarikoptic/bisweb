#!/usr/bin/env python3

# LICENSE
# 
# _This file is Copyright 2018 by the Image Processing and Analysis Group (BioImage Suite Team). Dept. of Radiology & Biomedical Imaging, Yale School of Medicine._
# 
# BioImage Suite Web is licensed under the Apache License, Version 2.0 (the "License");
# 
# - you may not use this software except in compliance with the License.
# - You may obtain a copy of the License at [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)
# 
# __Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.__
# 
# ENDLICENSE

import sys
try:
    import bisweb_path;
except ModuleNotFoundError:
    bisweb_path=0;
    
import biswebpython.core.bis_basemodule as bis_basemodule
import biswebpython.core.bis_objects as bis_objects

class regularizeObjectmap(bis_basemodule.baseModule):

    def __init__(self):
        super().__init__();
        self.name='regularizeObjectmap';
   
    def createDescription(self):
        return self.getModuleDescriptionFromFile('regularizeObjectmap');

    def directInvokeAlgorithm(self,vals):
        print('oooo invoking: regularizeObjectmap with vals', vals);

        input = self.inputs['input'];
        libbis=self.getDynamicLibraryWrapper();
        
        try:
            self.outputs['output'] = libbis.regularizeObjectmapWASM(input,
                                                                    paramobj={
                                                                        "smoothness" : vals['smoothness'],
                                                                        "convergence" : vals['convergence'],
                                                                        "iterations" : vals['iterations'],
                                                                        "internaliterations" : vals['internaliterations'],
                                                                    }, debug=self.parseBoolean(vals['debug']))
        except:
            e = sys.exc_info()[0]
            print('---- Failed to invoke algorithm',e);
            return False

        return True

if __name__ == '__main__':
    import biswebpython.core.bis_commandline as bis_commandline;
    sys.exit(bis_commandline.loadParse(regularizeObjectmap(),sys.argv,False));



    